from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DetailView, ListView, TemplateView, UpdateView)
from django.views.generic.edit import ModelFormMixin, ProcessFormView

from event.models import Event
from speaker.forms import (
    CreateSpeakerForm, EditSpeakerForm, UserSpeakerPortraitForm)
from speaker.models import PublishedSpeaker, Speaker
from talk.models import Talk


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

    def get_initial(self):
        initial = super().get_initial()
        initial['next'] = self.request.GET.get('next', None)
        return initial

    def form_valid(self, form):
        self.object = form.save(commit=True)
        next_url = form.cleaned_data.get('next', '')
        if next_url:
            return redirect('{}?next={}'.format(
                self.get_success_url(), next_url))
        return redirect(self.get_success_url())


class UserSpeakerProfileView(LoginRequiredMixin, UpdateView):
    model = Speaker
    template_name_suffix = '_user_profile'
    form_class = EditSpeakerForm
    success_url = reverse_lazy('user_speaker_profile')

    def get_object(self, queryset=None):
        return get_object_or_404(Speaker, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(UserSpeakerProfileView, self).get_context_data(**kwargs)
        context.update({
            'events_open_for_talk_submission': Event.objects.filter(
                submission_open=True
            ).order_by('start_time'),
            'sessions': Talk.objects.filter(
                draft_speaker=context['speaker']).select_related(
                'event', 'draft_speaker', 'published_speaker').order_by(
                '-event__title', 'title'),
            'speaker_image_height': settings.TALK_PUBLIC_SPEAKER_IMAGE_HEIGHT,
            'speaker_image_width': settings.TALK_PUBLIC_SPEAKER_IMAGE_WIDTH,
        })
        return context


class UserSpeakerPortraitUploadView(LoginRequiredMixin, UpdateView):
    model = Speaker
    form_class = UserSpeakerPortraitForm
    template_name_suffix = '_portrait_upload'
    success_url = reverse_lazy('user_speaker_profile')

    def get_object(self, queryset=None):
        return get_object_or_404(Speaker, user=self.request.user)

    def get_initial(self):
        initial = super().get_initial()
        initial['next'] = self.request.GET.get('next', None)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        next_url = context['form'].initial.get('next', '')
        if not next_url:
            next_url = self.success_url
        context.update({
            'next': next_url,
            'speaker_image_height': settings.TALK_PUBLIC_SPEAKER_IMAGE_HEIGHT,
            'speaker_image_width': settings.TALK_PUBLIC_SPEAKER_IMAGE_WIDTH,
        })
        return context

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
    model = PublishedSpeaker
    event = None

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, slug=self.kwargs.get('event'))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super(PublishedSpeakerListView, self).get_queryset().filter(
            event=self.event,
            talk__track__isnull=False  # TODO: replace with talk state check
        ).distinct().order_by('name')
