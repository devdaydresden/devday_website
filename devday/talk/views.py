from __future__ import unicode_literals

import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import AccessMixin, PermissionRequiredMixin
from django.contrib.auth.views import login
from django.core.exceptions import SuspiciousOperation
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.transaction import atomic
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView
from django.views.generic import TemplateView
from django.views.generic import View
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.edit import BaseFormView, UpdateView, CreateView, FormView
from django_file_form.forms import ExistingFile
from django_file_form.uploader import FileFormUploader
from pathlib import Path
from registration import signals
from registration.backends.hmac.views import RegistrationView

from attendee.models import Attendee
from talk.forms import CreateTalkForm, ExistingFileForm, TalkAuthenticationForm, CreateSpeakerForm, BecomeSpeakerForm, \
    EditTalkForm, TalkCommentForm, TalkVoteForm
from talk.models import Speaker, Talk, Vote, TalkComment

logger = logging.getLogger('talk')

User = get_user_model()


def submit_session_view(request):
    """
    This view presents a choice of links for anonymous users.

    """
    template_name = 'talk/submit_session.html'

    if not request.user.is_anonymous() and not "edit" in request.GET:
        try:
            request.user.attendee and request.user.attendee.speaker
            return redirect(reverse('create_session'))
        except (Attendee.DoesNotExist, Speaker.DoesNotExist):
            pass

    return login(request, template_name=template_name, authentication_form=TalkAuthenticationForm)


class SpeakerRegisteredView(TemplateView):
    template_name = "talk/speaker_registered.html"


class TalkSubmittedView(TemplateView):
    template_name = "talk/submitted.html"


class SpeakerRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated():
            return self.handle_no_permission()
        try:
            user.attendee and user.attendee.speaker
        except (Attendee.DoesNotExist, Speaker.DoesNotExist):
            raise SuspiciousOperation(_('Authenticated user must be a registered speaker'))
        return super(SpeakerRequiredMixin, self).dispatch(request, *args, **kwargs)


class CreateTalkView(SpeakerRequiredMixin, CreateView):
    template_name = "talk/create_talk.html"
    form_class = CreateTalkForm
    success_url = reverse_lazy('talk_submitted')

    def get_form_kwargs(self):
        form_kwargs = super(CreateTalkView, self).get_form_kwargs()
        form_kwargs['speaker'] = self.request.user.attendee.speaker
        return form_kwargs


class EditTalkView(SpeakerRequiredMixin, UpdateView):
    form_class = EditTalkForm
    success_url = reverse_lazy('speaker_profile')

    def get_queryset(self):
        return Talk.objects.filter(speaker=self.request.user.attendee.speaker)


class ExistingFileView(BaseFormView):
    form_class = ExistingFileForm

    def get_form_kwargs(self):
        form_kwargs = super(ExistingFileView, self).get_form_kwargs()

        speaker = Speaker.objects.get(id=self.kwargs['id'])

        if speaker.portrait:
            name = Path(speaker.portrait.name).name
            form_kwargs.update({
                'initial': dict(uploaded_image=ExistingFile(name))
            })

        return form_kwargs


class SpeakerProfileView(SpeakerRequiredMixin, TemplateView):
    template_name = "talk/speaker_profile.html"

    def get_context_data(self, **kwargs):
        context = super(SpeakerProfileView, self).get_context_data(**kwargs)
        attendee = Attendee.objects.filter(user=self.request.user).select_related('speaker').get()
        context.update({
            'attendee': attendee,
            'speaker': attendee.speaker,
            'talks': attendee.speaker.talk_set.all(),
        })
        return context


handle_upload = FileFormUploader()


class CreateSpeakerView(RegistrationView):
    template_name = 'talk/create_speaker.html'
    email_body_template = "talk/speaker_activation_email.txt"
    email_subject_template = "talk/speaker_activation_email_subject.txt"
    form_classes = {
        'anonymous': CreateSpeakerForm,
        'user': BecomeSpeakerForm,
        'attendee': BecomeSpeakerForm,
    }
    success_url = reverse_lazy('speaker_registered')

    def dispatch(self, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated():
            try:
                user.attendee and user.attendee.speaker
                return redirect(self.success_url)
            except Speaker.DoesNotExist:
                self.auth_level = 'attendee'
            except Attendee.DoesNotExist:
                self.auth_level = 'user'
        else:
            # noinspection PyAttributeOutsideInit
            self.auth_level = 'anonymous'
        return super(CreateSpeakerView, self).dispatch(*args, **kwargs)

    def get_form_class(self):
        return self.form_classes.get(self.auth_level, None)

    def get_email_context(self, activation_key):
        context = super(CreateSpeakerView, self).get_email_context(activation_key)
        context.update({'request': self.request})
        return context

    @atomic
    def form_valid(self, form):
        send_mail = False
        if self.auth_level == 'anonymous':
            email = form.cleaned_data['email']
            first_name = form.cleaned_data['firstname']
            last_name = form.cleaned_data['lastname']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = User.objects.create_user(
                    email=email, first_name=first_name, last_name=last_name, is_active=False)
                user.set_password(form.cleaned_data['password1'])
                signals.user_registered.send(sender=self.__class__,
                                             user=user,
                                             request=self.request)
                send_mail = True
        else:
            user = self.request.user

        if self.auth_level in ('user', 'anonymous'):
            user.first_name = form.cleaned_data['firstname']
            user.last_name = form.cleaned_data['lastname']
            user.save()
            attendee = Attendee.objects.create(user=user)
        else:
            attendee = user.attendee

        speaker = form.speakerform.save(commit=False)
        speaker.user = attendee
        speaker.save()
        try:
            form.speakerform.delete_temporary_files()
        except Exception as e:  # pragma: nocover
            # may be Windows error on Windows when file is locked by another process
            logger.warning("Error deleting temporary files: %s", e)

        if send_mail:
            self.send_activation_email(user)

        return redirect(self.success_url)


class CommitteeRequiredMixin(PermissionRequiredMixin):
    permission_required = ('talk.add_vote', 'talk.add_talkcomment')


class TalkOverview(CommitteeRequiredMixin, ListView):
    model = Talk
    template_name_suffix = '_overview'


class SpeakerDetails(CommitteeRequiredMixin, DetailView):
    model = Speaker
    template_name_suffix = '_details'


class TalkDetails(CommitteeRequiredMixin, DetailView):
    model = Talk
    template_name_suffix = '_details'

    def get_context_data(self, **kwargs):
        context = super(TalkDetails, self).get_context_data(**kwargs)
        talk = context['talk']
        try:
            user_vote = talk.vote_set.get(voter=self.request.user)
            user_score = user_vote.score
        except Vote.DoesNotExist:
            user_score = None
        context.update({
            'comment_form': TalkCommentForm(instance=talk),
            'user_vote': user_score,
            'average_votes': talk.get_average_votes()
        })
        return context


class SubmitTalkComment(CommitteeRequiredMixin, SingleObjectMixin, FormView):
    model = Talk
    form_class = TalkCommentForm
    http_method_names = ['post']

    def form_invalid(self, form):
        messages.warning(self.request, form.errors)
        # TODO: implement form_invalid for ajax calls
        return redirect(self.get_success_url())

    def form_valid(self, form):
        # TODO: implement form valid for ajax calls
        talk = self.get_object()
        talk.talkcomment_set.create(
            commenter=self.request.user, comment=form.cleaned_data['comment'],
            is_visible=form.cleaned_data['is_visible'])
        return super(SubmitTalkComment, self).form_valid(form)

    def get_success_url(self):
        talk = self.get_object()
        return reverse_lazy('talk_details', kwargs={'pk': talk.pk})

    def get_form_kwargs(self):
        kwargs = super(SubmitTalkComment, self).get_form_kwargs()
        kwargs['instance'] = self.get_object()
        return kwargs


class TalkVote(CommitteeRequiredMixin, UpdateView):
    model = Talk
    template_name_suffix = '_vote'
    form_class = TalkVoteForm

    def form_invalid(self, form):
        if self.request.is_ajax():
            return JsonResponse({'message': 'error', 'errors': form.errors})
        return super(TalkVote, self).form_invalid(form)

    def form_valid(self, form):
        talk = self.get_object()
        score = form.cleaned_data['score']
        try:
            vote = talk.vote_set.get(voter=self.request.user)
            vote.score = score
            vote.save()
        except Vote.DoesNotExist:
            talk.vote_set.create(voter=self.request.user, score=score)
        if self.request.is_ajax():
            return JsonResponse({'message': 'ok'})
        return super(TalkVote, self).form_valid(form)


class TalkVoteClear(CommitteeRequiredMixin, SingleObjectMixin, View):
    model = Talk
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        talk = self.get_object()
        talk.vote_set.filter(voter=request.user).delete()
        return JsonResponse({'message': 'vote deleted'})


class TalkCommentDelete(CommitteeRequiredMixin, SingleObjectMixin, View):
    model = TalkComment
    http_method_names = ['post']

    def get_queryset(self):
        return super(TalkCommentDelete, self).get_queryset().filter(commenter=self.request.user)

    def post(self, request, *args, **kwargs):
        self.get_object().delete()
        return JsonResponse({'message': 'comment deleted'})
