from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.generic import TemplateView


class AttendeeProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'attendee/profile.html'