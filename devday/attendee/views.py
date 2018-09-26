import csv
from StringIO import StringIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import login
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.transaction import atomic
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import TemplateView, View, UpdateView, DeleteView
from django.views.generic.list import BaseListView
from registration import signals
from registration.backends.hmac.views import RegistrationView

from attendee.forms import (AttendeeRegistrationForm, EventRegistrationForm,
                            RegistrationAuthenticationForm, AttendeeProfileForm)
from attendee.models import DevDayUser
from event.models import Event
from talk.models import Attendee, Talk

User = get_user_model()


class AttendeeProfileView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'attendee/profile.html'
    form_class = AttendeeProfileForm
    success_url = reverse_lazy('user_profile')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super(AttendeeProfileView, self).get_context_data(**kwargs)
        context['events'] = self.request.user.get_events().order_by('id')
        context['event_id'] = settings.EVENT_ID
        return context


class AttendeeRegistrationView(RegistrationView):
    form_classes = {
        'anonymous': AttendeeRegistrationForm,
        'user': EventRegistrationForm,
    }

    def create_attendee(self, user):
        event = Event.objects.filter(id=settings.EVENT_ID).first()
        attendee = Attendee(user=user, event=event)
        attendee.save()

    def dispatch(self, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated():
            if not user.get_attendee():
                self.auth_level = 'user'
                if self.request.method == 'POST':
                    self.create_attendee(self.request.user)
                    return redirect(reverse('register_success'))
            else:
                return redirect(reverse('register_success'))
        else:
            # noinspection PyAttributeOutsideInit
            self.auth_level = 'anonymous'
        return super(AttendeeRegistrationView, self).dispatch(*args, **kwargs)

    def get_form_class(self, request=None):
        return self.form_classes.get(self.auth_level, None)

    def get_email_context(self, activation_key):
        context = super(AttendeeRegistrationView, self).get_email_context(activation_key)
        context.update({'request': self.request})
        return context

    @atomic
    def register(self, form):
        user_form = form.get_user_form()

        user = user_form.save(commit=False)
        user.is_active = False
        if form.cleaned_data.get('accept_general_contact'):
            user.contact_permission_date = timezone.now()
        user.save()
        signals.user_registered.send(sender=self.__class__, user=user,
                                     request=self.request)

        self.create_attendee(user)

        self.send_activation_email(user)

        return user


class AttendeeCancelView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # remove attendee for user, event tuple
        Attendee.objects.filter(user=self.request.user,
                                event_id=kwargs['event']).delete()
        return HttpResponseRedirect(reverse('user_profile'))


class RegisterSuccessView(TemplateView):
    template_name = 'attendee/register_success.html'


def login_or_register_attendee_view(request):
    """
    This view presents a choice of links for anonymous users.

    """
    template_name = 'attendee/login_or_register.html'

    if not request.user.is_anonymous() and "edit" not in request.GET:
        try:
            # noinspection PyStatementEffect
            # request.user.attendee and request.user.attendee.speaker
            return redirect(reverse('registration_register'))
        except Attendee.DoesNotExist:
            pass

    return login(request, template_name=template_name, authentication_form=RegistrationAuthenticationForm)


class StaffUserMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class InactiveAttendeeView(StaffUserMixin, BaseListView):
    model = User

    def get_queryset(self):
        return super(InactiveAttendeeView, self).get_queryset().filter(is_active=False).order_by('email')

    def render_to_response(self, context):
        output = StringIO()
        try:
            writer = csv.writer(output, delimiter=';')
            writer.writerow(('Firstname', 'Lastname', 'Email', 'Date joined'))
            writer.writerows([(u.first_name.encode('utf8'), u.last_name.encode('utf8'), u.email.encode('utf8'),
                               u.date_joined.strftime("%Y-%m-%d %H:%M:%S"))
                              for u in context.get('object_list', [])])
            response = HttpResponse(output.getvalue(), content_type="txt/csv; charset=utf-8")
            response['Content-Disposition'] = 'attachment; filename=inactive.csv'
            return response
        finally:
            output.close()


class ContactableAttendeeView(StaffUserMixin, BaseListView):
    model = User

    def get_queryset(self):
        return super(ContactableAttendeeView, self).get_queryset().raw(
            '''
SELECT * FROM attendee_devdayuser WHERE contact_permission_date IS NOT NULL OR EXISTS (
  SELECT id FROM attendee_attendee WHERE event_id={:d} AND attendee_attendee.user_id=attendee_devdayuser.id
) ORDER BY email
'''.format(settings.EVENT_ID)
        )

    def render_to_response(self, context):
        output = StringIO()
        try:
            writer = csv.writer(output, delimiter=';')
            writer.writerow(('Email',))
            writer.writerows([(u.email.encode('utf8'),) for u in context.get('object_list', [])])
            response = HttpResponse(output.getvalue(), content_type="txt/csv; charset=utf-8")
            response['Content-Disposition'] = 'attachment; filename=contactable.csv'
            return response
        finally:
            output.close()


class AttendeeListView(StaffUserMixin, BaseListView):
    model = Attendee

    def get_queryset(self):
        return super(AttendeeListView, self).get_queryset().filter(
            event_id=settings.EVENT_ID).order_by("user__last_name", "user__first_name")

    def render_to_response(self, context):
        output = StringIO()
        try:
            writer = csv.writer(output, delimiter=';')
            writer.writerow(('Lastname', 'Firstname', 'Email', 'Date joined', 'Twitter', 'Phone', 'Position',
                             'Organization', 'Contact permission date', 'Info source'))
            writer.writerows([(
                attendee.user.last_name.encode('utf8'),
                attendee.user.first_name.encode('utf8'),
                attendee.user.email.encode('utf8'),
                attendee.user.date_joined.strftime("%Y-%m-%d %H:%M:%S"),
                attendee.user.twitter_handle.encode('utf8'),
                attendee.user.phone.encode('utf8'),
                attendee.user.position.encode('utf8'),
                attendee.user.organization.encode('utf8'),
                attendee.user.contact_permission_date.strftime(
                    "%Y-%m-%d %H:%M:%S") if attendee.user.contact_permission_date else "",
                attendee.source.encode('utf8'),
            ) for attendee in context.get('object_list', [])])
            response = HttpResponse(output.getvalue(), content_type="txt/csv; charset=utf-8")
            response['Content-Disposition'] = 'attachment; filename=attendees.csv'
            return response
        finally:
            output.close()


class AttendeeDeleteView(LoginRequiredMixin, DeleteView):
    model = DevDayUser

    def get_object(self, queryset=None):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        if Talk.objects.filter(speaker__user__user=user).count() > 0:
            return HttpResponse(status=409)
        return super(AttendeeDeleteView, self).delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('pages-root')
