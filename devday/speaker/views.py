from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, UpdateView

from speaker.forms import (
    CreateSpeakerForm, EditSpeakerForm, UserSpeakerPortraitForm)
from speaker.models import Speaker


class CreateSpeakerView(CreateView, LoginRequiredMixin):
    model = Speaker
    form_class = CreateSpeakerForm

    def dispatch(self, request, *args, **kwargs):
        if Speaker.objects.filter(user=request.user).exists():
            return redirect('user_speaker_profile')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('user_speaker_profile')


class UserSpeakerProfileView(UpdateView, LoginRequiredMixin):
    model = Speaker
    template_name_suffix = '_user_profile'
    form_class = EditSpeakerForm

    def get_object(self, queryset=None):
        return get_object_or_404(Speaker, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'profile_image_form': UserSpeakerPortraitForm(self.object)
        })
        return context


class UserSpeakerPortraitUploadView(UpdateView,
                                    LoginRequiredMixin):
    model = Speaker
    form_class = UserSpeakerPortraitForm

    def get_object(self, queryset=None):
        return get_object_or_404(Speaker, user=self.request.user)

    def get_success_url(self):
        return reverse('user_speaker_profile')
