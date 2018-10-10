import csv
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import login
from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse, reverse_lazy
from django.db import IntegrityError
from django.db.transaction import atomic
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView, View, UpdateView, DeleteView
from django.views.generic.edit import FormView
from django.views.generic.list import BaseListView
from django_registration import signals
from django_registration.backends.activation.views import RegistrationView

from attendee.forms import (AttendeeRegistrationForm, CheckInAttendeeForm,
                            EventRegistrationForm,
                            RegistrationAuthenticationForm,
                            AttendeeProfileForm)
from .models import DevDayUser
from event.models import Event
from talk.models import Attendee, Talk

User = get_user_model()


class AttendeeQRCodeMixIn:
    def attendee_qrcode_context(self, context):
        attendee = Attendee.objects.filter(
            user=self.request.user, event=Event.objects.current_event()
            ).first()
        if attendee:
            context['checked_in'] = attendee.checked_in is not None
            if context['checked_in']:
                context['message'] = _('You are already checked in.')
                context['message_code'] = 'already'
            else:
                context['url'] = self.request.build_absolute_uri(
                    attendee.get_checkin_url())
                context['checkin_code'] = attendee.checkin_code
                context['message_code'] = 'OK'
        else:
            context['checked_in'] = False
            context['message'] = \
                _('You are not registered for the current event.')
            context['message_code'] = 'notregistered'


class AttendeeProfileView(LoginRequiredMixin, AttendeeQRCodeMixIn, UpdateView):
    model = User
    template_name = 'attendee/profile.html'
    form_class = AttendeeProfileForm
    success_url = reverse_lazy('user_profile')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super(AttendeeProfileView, self).get_context_data(**kwargs)
        context['events'] = self.request.user.get_events().order_by('id')
        context['current_event'] = Event.objects.current_event()
        context['event_id'] = Event.objects.current_event_id()
        self.attendee_qrcode_context(context)
        return context


class AttendeeRegistrationView(RegistrationView):
    form_classes = {
        'anonymous': AttendeeRegistrationForm,
        'user': EventRegistrationForm,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_level = None

    def create_attendee(self, user, event):
        attendee = Attendee(user=user, event=event)
        attendee.save()
        return attendee

    def dispatch(self, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            current_event = Event.objects.current_event()
            if not user.get_attendee(event=current_event):
                self.auth_level = 'user'
                if self.request.method == 'POST':
                    self.create_attendee(
                        self.request.user, event=current_event)
                    return redirect(self.get_success_url())
            else:
                return redirect(self.get_success_url())
        else:
            # noinspection PyAttributeOutsideInit
            self.auth_level = 'anonymous'
        return super(AttendeeRegistrationView, self).dispatch(*args, **kwargs)

    def get_success_url(self, user=None):
        if self.auth_level == 'anonymous':
            return reverse_lazy('django_registration_complete')
        return reverse_lazy('register_success')

    def get_form_class(self, request=None):
        return self.form_classes.get(self.auth_level, None)

    def get_email_context(self, activation_key):
        context = super(AttendeeRegistrationView, self).get_email_context(
            activation_key)
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

        attendee = self.create_attendee(user, Event.objects.current_event())
        attendee.source = form.cleaned_data.get('source')
        attendee.save()

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

    if not request.user.is_anonymous and "edit" not in request.GET:
        try:
            # noinspection PyStatementEffect
            # request.user.attendee and request.user.attendee.speaker
            return redirect(reverse('registration_register'))
        except Attendee.DoesNotExist:
            pass

    return login(request, template_name=template_name,
                 authentication_form=RegistrationAuthenticationForm)


class StaffUserMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class InactiveAttendeeView(StaffUserMixin, BaseListView):
    model = User

    def get_queryset(self):
        return super().get_queryset().filter(is_active=False).order_by('email')

    def render_to_response(self, context):
        output = StringIO()
        try:
            writer = csv.writer(output, delimiter=';')
            writer.writerow(('Firstname', 'Lastname', 'Email', 'Date joined'))
            writer.writerows([(
                u.first_name.encode('utf8'), u.last_name.encode('utf8'),
                u.email.encode('utf8'),
                u.date_joined.strftime("%Y-%m-%d %H:%M:%S"))
                              for u in context.get('object_list', [])])
            response = HttpResponse(output.getvalue(),
                                    content_type="txt/csv; charset=utf-8")
            response['Content-Disposition'] \
                = 'attachment; filename=inactive.csv'
            return response
        finally:
            output.close()


class ContactableAttendeeView(StaffUserMixin, BaseListView):
    model = User

    def get_queryset(self):
        return super(ContactableAttendeeView, self).get_queryset().raw(
            '''
SELECT * FROM attendee_devdayuser WHERE contact_permission_date IS NOT NULL
  OR EXISTS (
    SELECT id FROM attendee_attendee WHERE event_id={:d}
      AND attendee_attendee.user_id=attendee_devdayuser.id
) ORDER BY email
'''.format(Event.objects.current_event_id())
        )

    def render_to_response(self, context):
        output = StringIO()
        try:
            writer = csv.writer(output, delimiter=';')
            writer.writerow(('Email',))
            writer.writerows([(u.email.encode('utf8'),)
                              for u in context.get('object_list', [])])
            response = HttpResponse(
                output.getvalue(), content_type="txt/csv; charset=utf-8")
            response['Content-Disposition'] \
                = 'attachment; filename=contactable.csv'
            return response
        finally:
            output.close()


class AttendeeListView(StaffUserMixin, BaseListView):
    model = Attendee

    def get_queryset(self):
        return super(AttendeeListView, self).get_queryset().filter(
            event_id=Event.objects.current_event_id()
        ).order_by("user__last_name", "user__first_name")

    def render_to_response(self, context):
        output = StringIO()
        try:
            writer = csv.writer(output, delimiter=';')
            writer.writerow(('Lastname', 'Firstname', 'Email', 'Date joined',
                             'Twitter', 'Phone', 'Position', 'Organization',
                             'Contact permission date', 'Info source'))
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
                    "%Y-%m-%d %H:%M:%S"
                    ) if attendee.user.contact_permission_date else "",
                attendee.source.encode('utf8'),
            ) for attendee in context.get('object_list', [])])
            response = HttpResponse(
                output.getvalue(), content_type="txt/csv; charset=utf-8")
            response['Content-Disposition'] \
                = 'attachment; filename=attendees.csv'
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


class CheckInAttendeeView(StaffUserMixin, SuccessMessageMixin, FormView):
    template_name = 'attendee/checkin.html'
    form_class = CheckInAttendeeForm
    success_url = reverse_lazy('attendee_checkin')
    success_message = _('{first_name} {last_name} <{email}>'
                        ' has been checked in successfully to'
                        ' {event}!')

    def form_valid(self, form):
        a = form.cleaned_data['attendee']
        a.check_in()
        a.save()
        return super().form_valid(form)

    def get_success_message(self, cleaned_data):
        a = cleaned_data['attendee']
        u = a.user
        e = a.event
        m = {
            'first_name': u.first_name,
            'last_name': u.last_name,
            'email': u.email,
            'event': e.title,
        }
        return self.success_message.format_map(m)


class CheckInAttendeeQRView(LoginRequiredMixin, AttendeeQRCodeMixIn,
                            TemplateView):
    template_name = 'attendee/checkin_qrcode.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.attendee_qrcode_context(context)
        return context


class CheckInAttendeeUrlView(StaffUserMixin, TemplateView):
    template_name = 'attendee/checkin_result.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        id = self.kwargs['id']
        verification = self.kwargs['verification']
        if not Attendee.objects.is_verification_valid(id, verification):
            context['checkin_result'] = _('Invalid verification URL')
            context['checkin_message'] = _('Try again scanning the QR code.')
            return context
        try:
            attendee = Attendee.objects.get(id=id)
        except ObjectDoesNotExist:
            context['checkin_result'] = _('Attendee not found')
            context['checkin_message'] = \
                _('The attendee is (no longer) registered.')
            return context
        try:
            attendee.check_in()
            attendee.save()
        except IntegrityError:
            context['checkin_result'] = _('Already checked in')
            context['checkin_message'] = \
                _('Attendee {} has checked in at {}.') \
                .format(attendee.user,
                        attendee.checked_in.strftime('%H:%M %d.%m.%y'))
            return context
        context['checkin_result'] = 'Welcome!'
        context['checkin_message'] = \
            _('Attendee {} was successfully checked in.').format(attendee.user)
        return context
