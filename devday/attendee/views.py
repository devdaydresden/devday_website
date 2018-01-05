from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import login
from django.core.urlresolvers import reverse
from django.db.transaction import atomic
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, View
from django.http import HttpResponseRedirect
from registration import signals
from registration.backends.hmac.views import RegistrationView

from attendee.forms import (AttendeeRegistrationForm, EventRegistrationForm,
                            RegistrationAuthenticationForm)
from event.models import Event
from talk.models import Attendee

User = get_user_model()


class AttendeeProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'attendee/profile.html'

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
            #request.user.attendee and request.user.attendee.speaker
            return redirect(reverse('registration_register'))
        except (Attendee.DoesNotExist):
            pass

    return login(request, template_name=template_name, authentication_form=RegistrationAuthenticationForm)
