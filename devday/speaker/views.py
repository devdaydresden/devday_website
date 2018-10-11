from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView

from speaker.forms import (
    CreateSpeakerForm, EditSpeakerForm, UserSpeakerPortraitForm)
from speaker.models import Speaker


class NoSpeakerYetMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if Speaker.objects.filter(user=request.user).exists():
            return redirect('user_speaker_profile')
        return super(NoSpeakerYetMixin, self).dispatch(
            request, *args, **kwargs)


class CreateSpeakerView(LoginRequiredMixin, NoSpeakerYetMixin, CreateView):
    model = Speaker
    form_class = CreateSpeakerForm
    success_url = reverse_lazy('user_speaker_profile')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class UserSpeakerProfileView(LoginRequiredMixin, UpdateView):
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


class UserSpeakerPortraitUploadView(LoginRequiredMixin, UpdateView):
    model = Speaker
    form_class = UserSpeakerPortraitForm

    def get_object(self, queryset=None):
        return get_object_or_404(Speaker, user=self.request.user)

    def get_success_url(self):
        return reverse('user_speaker_profile')

    def form_valid(self, form):
        self.object = form.save()
        if self.request.is_ajax():
            return JsonResponse({"image_url": self.object.portrait.url})
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        if self.request.is_ajax():
            return JsonResponse({"errors": form.errors}, status=400)
        return super(UserSpeakerPortraitUploadView, self).form_invalid(form)
