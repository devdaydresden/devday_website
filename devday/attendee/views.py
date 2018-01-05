from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.db.transaction import atomic
from django.utils import timezone
from django.views.generic import TemplateView, View
from django.http import HttpResponseRedirect
from registration import signals
from registration.backends.hmac.views import RegistrationView

from attendee.forms import AttendeeRegistrationForm
from event.models import Event
from talk.models import Attendee

User = get_user_model()


class AttendeeProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'attendee/profile.html'

    def get_context_data(self, **kwargs):
        context = super(AttendeeProfileView, self).get_context_data(**kwargs)
        context['events'] = self.request.user.get_events()
        return context

class AttendeeRegistrationView(RegistrationView):
    form_class = AttendeeRegistrationForm

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
        signals.user_registered.send(sender=self.__class__, user=user, request=self.request)

        attendee = form.get_attendee_form().save(commit=False)
        attendee.user = user
        attendee.event = Event.objects.filter(id=settings.EVENT_ID).first()
        if form.cleaned_data.get('accept_devday_contact'):
            attendee.contact_permission_date = timezone.now()
        attendee.save()

        self.send_activation_email(user)

        return user

class AttendeeCancelView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # remove attendee for user, event tuple
        Attendee.objects.filter(user=self.request.user, event_id=kwargs['event']).delete()
        return HttpResponseRedirect(reverse('user_profile'))
