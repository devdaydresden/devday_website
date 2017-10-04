from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.transaction import atomic
from django.utils import timezone
from django.views.generic import TemplateView
from registration import signals
from registration.backends.hmac.views import RegistrationView

from attendee.forms import AttendeeRegistrationForm

from talk.models import Attendee

User = get_user_model()


class AttendeeProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'attendee/profile.html'

    def get_context_data(self, **kwargs):
        context = super(AttendeeProfileView, self).get_context_data(**kwargs)
        context['attendees'] = Attendee.objects.filter(user=self.request.user)
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
        if form.cleaned_data.get('accept_devday_contact'):
            attendee.contact_permission_date = timezone.now()
        attendee.save()

        self.send_activation_email(user)

        return user
