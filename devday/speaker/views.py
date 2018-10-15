from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, TemplateView, \
    DetailView, ListView
from django.views.generic.edit import ModelFormMixin, ProcessFormView

from event.models import Event
from speaker.forms import (
    CreateSpeakerForm, EditSpeakerForm, UserSpeakerPortraitForm)
from speaker.models import Speaker, PublishedSpeaker


class NoSpeakerYetMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if Speaker.objects.filter(user=request.user).exists():
            return redirect('user_speaker_profile')
        # noinspection PyUnresolvedReferences
        return super(NoSpeakerYetMixin, self).dispatch(
            request, *args, **kwargs)


class CreateSpeakerView(LoginRequiredMixin, NoSpeakerYetMixin, CreateView):
    model = Speaker
    form_class = CreateSpeakerForm
    success_url = reverse_lazy('upload_user_speaker_portrait')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class UserSpeakerProfileView(LoginRequiredMixin, UpdateView):
    model = Speaker
    template_name_suffix = '_user_profile'
    form_class = EditSpeakerForm
    success_url = reverse_lazy('user_speaker_profile')

    def get_object(self, queryset=None):
        return get_object_or_404(Speaker, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(UserSpeakerProfileView, self).get_context_data(**kwargs)
        context['events_open_for_talk_submission'] = Event.objects.filter(
            submission_open=True
        ).order_by('start_time')
        return context


class UserSpeakerPortraitUploadView(LoginRequiredMixin, UpdateView):
    model = Speaker
    form_class = UserSpeakerPortraitForm
    template_name_suffix = '_portrait_upload'
    success_url = reverse_lazy('user_speaker_profile')

    def get_object(self, queryset=None):
        return get_object_or_404(Speaker, user=self.request.user)

    def form_valid(self, form):
        self.object = form.save()
        if self.request.is_ajax():
            return JsonResponse({"image_url": self.object.portrait.url})
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        if self.request.is_ajax():
            return JsonResponse({"errors": form.errors}, status=400)
        return super(UserSpeakerPortraitUploadView, self).form_invalid(form)


class UserSpeakerPortraitDeleteView(
    LoginRequiredMixin, ModelFormMixin, ProcessFormView, TemplateView
):
    model = Speaker
    template_name = "speaker/speaker_portrait_confirm_delete.html"
    fields = []
    success_url = reverse_lazy('user_speaker_profile')
    object = None

    def get_object(self, queryset=None):
        self.object = get_object_or_404(Speaker, user=self.request.user)
        if self.object.portrait:
            return self.object
        raise Http404()

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(UserSpeakerPortraitDeleteView, self).get(
            request, *args, **kwargs)

    def form_valid(self, form):
        speaker = self.get_object()
        speaker.portrait.delete()

        if self.request.is_ajax():
            return HttpResponse(content_type=None, status=204)
        return redirect(self.success_url)


class PublishedSpeakerDetailView(DetailView):
    model = PublishedSpeaker

    def get_queryset(self):
        return super(PublishedSpeakerDetailView, self).get_queryset().filter(
            talk__track__isnull=False  # TODO: replace with talk state check
        ).prefetch_related('talk_set').distinct()

    def get_context_data(self, **kwargs):
        context = super(PublishedSpeakerDetailView, self).get_context_data(
            **kwargs)
        context['talks'] = context['publishedspeaker'].talk_set.filter(
            track__isnull=False  # TODO: replace with talk state check
        )
        context['event'] = get_object_or_404(
            Event, slug=self.kwargs.get('event'))
        return context


class PublishedSpeakerListView(ListView):
    model = Speaker

    def get_queryset(self):
        return super(PublishedSpeakerListView, self).get_queryset().filter(
            talk__track__isnull=False  # TODO: replace with talk state check
        ).order_by('name')
