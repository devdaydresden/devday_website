from __future__ import unicode_literals

import logging
import xml.etree.ElementTree as ET

from datetime import datetime, date, timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import AccessMixin, PermissionRequiredMixin
from django.contrib.auth.views import login
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Avg, Count, Sum, Min, Max
from django.db.transaction import atomic
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify
from django.views.generic import ListView, RedirectView
from django.views.generic import TemplateView
from django.views.generic import View
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.edit import BaseFormView, UpdateView, CreateView, FormView
from django.views.generic.list import BaseListView
from django_file_form.forms import ExistingFile
from django_file_form.uploader import FileFormUploader
from pathlib import Path
from registration import signals
from registration.backends.hmac.views import RegistrationView

from attendee.models import Attendee
from event.models import Event
from talk.forms import CreateTalkForm, ExistingFileForm, TalkAuthenticationForm, CreateSpeakerForm, BecomeSpeakerForm, \
    EditTalkForm, TalkCommentForm, TalkVoteForm, TalkSpeakerCommentForm, EditSpeakerForm
from talk.models import Speaker, Talk, Vote, TalkComment, Room, TimeSlot, TalkSlot

logger = logging.getLogger('talk')

User = get_user_model()

XML_TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%S%z'


def submit_session_view(request):
    """
    This view presents a choice of links for anonymous users.

    """
    template_name = 'talk/submit_session.html'

    if not request.user.is_anonymous() and not "edit" in request.GET:
        try:
            # noinspection PyStatementEffect
            # request.user.attendee and request.user.attendee.speaker
            return redirect(reverse('create_session'))
        except (Attendee.DoesNotExist, Speaker.DoesNotExist):
            pass

    return login(request, template_name=template_name, authentication_form=TalkAuthenticationForm)


class TalkSubmissionOpenMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if not settings.TALK_SUBMISSION_OPEN:
            return redirect('talk_submission_closed')
        # noinspection PyUnresolvedReferences
        return super(TalkSubmissionOpenMixin, self).dispatch(request, *args, **kwargs)


class TalkSubmissionClosed(TemplateView):
    template_name = 'talk/submission_closed.html'


class SpeakerRegisteredView(TemplateView):
    template_name = "talk/speaker_registered.html"


class SpeakerRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated():
            return self.handle_no_permission()
        if not user.get_speaker():
            return redirect(reverse('create_speaker'))
        # noinspection PyUnresolvedReferences
        return super(SpeakerRequiredMixin, self).dispatch(request, *args, **kwargs)


class TalkSubmittedView(SpeakerRequiredMixin, TemplateView):
    template_name = "talk/submitted.html"

    def get_context_data(self, **kwargs):
        context = super(TalkSubmittedView, self).get_context_data(**kwargs)
        context['speaker'] = self.request.user.get_speaker()
        return context


class CreateTalkView(TalkSubmissionOpenMixin, SpeakerRequiredMixin, CreateView):
    template_name = "talk/create_talk.html"
    form_class = CreateTalkForm
    success_url = reverse_lazy('talk_submitted')

    def get_form_kwargs(self):
        form_kwargs = super(CreateTalkView, self).get_form_kwargs()
        form_kwargs['speaker'] = self.request.user.get_speaker()
        return form_kwargs


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


class SpeakerProfileView(SpeakerRequiredMixin, UpdateView):
    model = Speaker
    template_name_suffix = '_profile'
    form_class = EditSpeakerForm

    def get_context_data(self, **kwargs):
        context = super(SpeakerProfileView, self).get_context_data(**kwargs)
        speaker = self.get_object()
        attendee = speaker.user
        context.update({
            'attendee': attendee,
            'speaker': speaker,
            'talks': attendee.speaker.talk_set.all(),
        })
        return context

    def get_form_kwargs(self):
        kwargs = super(SpeakerProfileView, self).get_form_kwargs()
        kwargs['instance'] = self.get_object()
        return kwargs

    def get_queryset(self):
        return super(SpeakerProfileView, self).get_queryset().select_related('user', 'user__user').filter(
            user__user=self.request.user)

    def get_success_url(self):
        return reverse('speaker_profile', kwargs={'pk': self.object.pk})


handle_upload = FileFormUploader()


class CreateSpeakerView(TalkSubmissionOpenMixin, RegistrationView):
    template_name = 'talk/create_speaker.html'
    email_body_template = "talk/speaker_activation_email.txt"
    email_subject_template = "talk/speaker_activation_email_subject.txt"
    form_classes = {
        'anonymous': CreateSpeakerForm,
        'user': BecomeSpeakerForm,
        'attendee': BecomeSpeakerForm,
    }

    def dispatch(self, *args, **kwargs):
        user = self.request.user
        event = Event.objects.get(pk=settings.EVENT_ID)
        if user.is_authenticated():
            if not user.get_attendee():
                self.auth_level = 'user'
            elif not user.get_speaker():
                self.auth_level = 'attendee'
            else:
                return redirect(self.get_success_url())
        else:
            # noinspection PyAttributeOutsideInit
            self.auth_level = 'anonymous'
        return super(CreateSpeakerView, self).dispatch(*args, **kwargs)

    def get_form_class(self):
        return self.form_classes.get(self.auth_level, None)

    def get_form_kwargs(self):
        kw = super(CreateSpeakerView, self).get_form_kwargs()
        kw['devdayuserform_model'] = self.request.user
        return kw

    def get_email_context(self, activation_key):
        context = super(CreateSpeakerView, self).get_email_context(activation_key)
        context.update({'request': self.request})
        return context

    def register(self, form):
        r = super(CreateSpeakerView, self).register(form)
        return r

    def get_success_url(self):
        if self.request.user.is_active:
            return reverse('create_session')
        return reverse_lazy('speaker_registered')

    @atomic
    def form_valid(self, form):
        do_send_mail = False
        if self.auth_level == 'anonymous':
            user = User.objects.create_user(
                email=form.cleaned_data['email'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                phone=form.cleaned_data['phone'],
                password=form.cleaned_data['password1'],
                contact_permission_date=datetime.now(),
                is_active=False)
            signals.user_registered.send(sender=self.__class__,
                                         user=user,
                                         request=self.request)
            do_send_mail = True
        elif self.auth_level in ('user', 'attendee'):
            user = form.devdayuserform.save()
        else:
            user = self.request.user

        if self.auth_level in ('anonymous', 'user'):
            attendee = Attendee.objects.create(user=user, event_id=settings.EVENT_ID)
        else:
            attendee = user.attendees.get(event_id=settings.EVENT_ID)

        speaker = form.speakerform.save(commit=False)
        speaker.user = attendee
        speaker.save()
        try:
            form.speakerform.delete_temporary_files()
        except Exception as e:  # pragma: nocover
            # may be Windows error on Windows when file is locked by another process
            logger.warning("Error deleting temporary files: %s", e)

        if do_send_mail:
            self.send_activation_email(user)

        return redirect(self.get_success_url())


class CommitteeRequiredMixin(PermissionRequiredMixin):
    permission_required = ('talk.add_vote', 'talk.add_talkcomment')


class TalkDetails(DetailView):
    model = Talk
    template_name_suffix = '_details'

    def dispatch(self, request, *args, **kwargs):
        talk = get_object_or_404(Talk, pk=self.kwargs.get('pk'))
        event = get_object_or_404(Event, slug=self.kwargs.get('event'))

        if slugify(talk.title) != kwargs.get('slug') or event != talk.event:
            return HttpResponseRedirect('/{}/talk/{}/{}'.format(event.slug, slugify(talk.title), talk.id))
        return super(TalkDetails, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TalkDetails, self).get_context_data(**kwargs)
        context.update({
            'speaker': context['talk'].speaker,
        })
        return context


class CommitteeTalkOverview(CommitteeRequiredMixin, ListView):
    model = Talk
    template_name_suffix = '_committee_overview'

    ORDER_MAP = {
        'speaker': 'speaker__user__user__first_name',
        'score': 'average_score',
        'score_sum': 'vote_sum',
    }

    def get_queryset(self):
        qs = super(CommitteeTalkOverview, self).get_queryset().filter(
            speaker__user__event_id=settings.EVENT_ID).annotate(
            average_score=Avg('vote__score'),
            vote_sum=Sum('vote__score'),
            vote_count=Count('vote__id')).select_related(
            'speaker', 'speaker__user', 'speaker__user__user').order_by('title')
        sort_order = self.request.GET.get('sort_order', 'title')
        sort_order = CommitteeTalkOverview.ORDER_MAP.get(sort_order, sort_order)
        if self.request.GET.get('sort_dir') == 'desc':
            sort_order = '-{}'.format(sort_order)
        return qs.order_by(sort_order)

    def get_context_data(self, **kwargs):
        context = super(CommitteeTalkOverview, self).get_context_data(**kwargs)
        talk_list = context['talk_list']
        for item in Talk.objects.values('id').annotate(comment_count=Count('talkcomment__id')).all():
            for talk in talk_list:
                if item['id'] == talk.id:
                    setattr(talk, 'comment_count', item['comment_count'])
        context.update({
            'sort_order': self.request.GET.get('sort_order', 'title'),
            'sort_dir': self.request.GET.get('sort_dir', 'asc'),
        })
        return context


class CommitteeSpeakerDetails(CommitteeRequiredMixin, DetailView):
    model = Speaker
    template_name_suffix = '_details'


class SpeakerPublic(DetailView):
    model = Speaker
    template_name_suffix = '_public'

    def get_queryset(self):
        return super(SpeakerPublic, self).get_queryset().filter(talk__track__isnull=False).prefetch_related('talk_set')

    def get_context_data(self, **kwargs):
        context = super(SpeakerPublic, self).get_context_data(**kwargs)
        context['talks'] = context['speaker'].talk_set.filter(track__isnull=False)
        return context


class TalkListView(ListView):
    model = Talk

    def dispatch(self, request, *args, **kwargs):
        event = self.kwargs.get('event')
        if not event:
            event = Event.objects.get(pk=settings.EVENT_ID)
            return HttpResponseRedirect('/{}/talk/'.format(event.slug))
        return super(TalkListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        event = get_object_or_404(Event, slug=self.kwargs.get('event'))
        return super(TalkListView, self).get_queryset().filter(track__isnull=False,
                                                               speaker__user__event=event,
                                                               talkslot__time__event=event).select_related(
            'track',
            'speaker', 'speaker__user', 'speaker__user__event',
            'speaker__user__user', 'speaker__user__event__slug',
            'talkslot', 'talkslot__time', 'talkslot__room'
        ).order_by('talkslot__time__start_time', 'talkslot__room__name')

    def get_context_data(self, **kwargs):
        context = super(TalkListView, self).get_context_data(**kwargs)
        event = get_object_or_404(Event, slug=self.kwargs.get('event'))
        talks = context.get('talk_list', [])
        talks_by_time_and_room = {}
        talks_by_room_and_time = {}
        unscheduled = []
        has_footage = Talk.objects.filter(
            speaker__user__event=event,
            track__isnull=False).filter(media__isnull=False).select_related(
            'speaker', 'speaker__user', 'speaker__user__user', 'media'
        ).count() > 0
        for talk in talks:
            try:
                # build dictionary grouped by time and room (md and lg display)
                talks_by_time_and_room.setdefault(talk.talkslot.time, []).append(talk)
                # build dictionary grouped by room and time (sm and xs display)
                talks_by_room_and_time.setdefault(talk.talkslot.room, []).append(talk)
            except TalkSlot.DoesNotExist:
                unscheduled.append(talk)
        context.update(
            {
                'event': event,
                'talks_by_time_and_room': talks_by_time_and_room,
                'talks_by_room_and_time': talks_by_room_and_time,
                'unscheduled': unscheduled,
                'rooms': Room.objects.all(),
                'times': TimeSlot.objects.filter(event=event),
                'has_footage': has_footage,
            }
        )
        return context


class TalkListPreviewView(ListView):
    model = Talk
    template_name_suffix = "_list_preview"

    def get_queryset(self):
        event = get_object_or_404(Event, slug=self.kwargs.get('event'))
        return super(TalkListPreviewView, self).get_queryset().filter(track__isnull=False,
                                                                      speaker__user__event=event).select_related(
            'speaker__user__event', 'speaker__user__event__slug',
            'track',
            'speaker', 'speaker__user', 'speaker__user__user'
        ).order_by('title')


class TalkVideoView(ListView):
    model = Talk
    template_name_suffix = '_videos'

    def __init__(self, *args, **kwargs):
        self._event = None
        super(TalkVideoView, self).__init__(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self._event = get_object_or_404(Event, slug=self.kwargs.get('event'))
        return super(TalkVideoView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        return super(TalkVideoView, self).get_queryset().filter(
            speaker__user__event=self._event,
            track__isnull=False).filter(media__isnull=False).select_related(
            'speaker', 'speaker__user', 'speaker__user__user', 'media'
        ).order_by('title')

    def get_context_data(self, **kwargs):
        context = super(TalkVideoView, self).get_context_data(**kwargs)
        context['event'] = self._event.title
        return context


class InfoBeamerXMLView(BaseListView):
    model = Talk

    def dispatch(self, request, *args, **kwargs):
        event = self.kwargs.get('event')
        if not event:
            event = Event.objects.get(pk=settings.EVENT_ID)
            return HttpResponseRedirect('/{}/schedule.xml'.format(event.slug))
        return super(InfoBeamerXMLView, self).dispatch(request, *args, **kwargs)

    def recalculate_timestamp(self, timestamp, context):
        if 'starttoday' in self.request.GET:
            start_time = context.get('min_time')
            delta = date.today() - start_time.date()
        else:
            delta = timedelta()
        delta += timedelta(hours=int(self.request.GET.get('offsethours', '0')))
        local_time = timezone.localtime(timestamp + delta, timezone.get_default_timezone())
        return local_time

    def to_xml_timestamp(self, timestamp, context):
        formatted = self.recalculate_timestamp(timestamp, context).strftime(XML_TIMESTAMP_FORMAT)
        return "%s:%s" % (formatted[:-2], formatted[-2:])

    def to_xml_localtime(self, timestamp, context):
        return self.recalculate_timestamp(timestamp, context).strftime("%H:%M")

    def to_xml_date(self, timestamp, context):
        return self.recalculate_timestamp(timestamp, context).strftime("%Y-%m-%d")

    def get_queryset(self):
        event = get_object_or_404(Event, slug=self.kwargs.get('event'))
        return super(InfoBeamerXMLView, self).get_queryset().filter(track__isnull=False,
                                                                    speaker__user__event=event,
                                                                    talkslot__time__event=event).select_related(
            'track',
            'speaker', 'speaker__user', 'speaker__user__user',
            'talkslot', 'talkslot__time', 'talkslot__room'
        ).order_by('talkslot__time__start_time', 'talkslot__room__name')

    def get_context_data(self, **kwargs):
        context = super(InfoBeamerXMLView, self).get_context_data(**kwargs)
        event = get_object_or_404(Event, slug=self.kwargs.get('event'))
        time_range = TimeSlot.objects.filter(event=event).aggregate(Min('start_time'), Max('end_time'))
        context['min_time'] = time_range['start_time__min']
        context['max_time'] = time_range['end_time__max']
        talks = context.get('talk_list', [])
        talks_by_room_and_time = {}
        for talk in talks:
            try:
                # build dictionary grouped by room and time (sm and xs display)
                talks_by_room_and_time.setdefault(talk.talkslot.room, []).append(talk)
            except TalkSlot.DoesNotExist:
                continue
        context.update(
            {
                'event': event,
                'talks_by_room_and_time': talks_by_room_and_time,
                'rooms': Room.objects.all(),
                'times': TimeSlot.objects.filter(event=event)
            }
        )
        return context

    def render_to_response(self, context, **response_kwargs):
        event = context['event']
        schedule_xml = ET.Element('schedule')
        # TODO: use event argument and render proper event title
        ET.SubElement(schedule_xml, 'version').text = event.title
        conference = ET.SubElement(schedule_xml, 'conference')
        ET.SubElement(conference, 'acronym').text = 'DevDay'
        ET.SubElement(conference, 'title').text = event.title
        ET.SubElement(conference, 'start').text = self.to_xml_date(event.start_time, context)
        ET.SubElement(conference, 'end').text = self.to_xml_date(event.end_time, context)
        ET.SubElement(conference, 'days').text = '1'  # FIXME compute days
        ET.SubElement(conference, 'timeslot_duration').text = '00:15'
        day_xml = ET.SubElement(schedule_xml, 'day', index='1',
                                date=self.to_xml_date(context['min_time'], context),
                                start=self.to_xml_timestamp(context['min_time'], context),
                                end=self.to_xml_timestamp(context['max_time'], context))
        for room in context['rooms']:
            room_xml = ET.SubElement(day_xml, 'room', name=room.name)
            room_talks = context['talks_by_room_and_time']
            if room in room_talks:
                for talk in room_talks[room]:
                    event_xml = ET.SubElement(room_xml, 'event', guid=str(talk.pk), id=str(talk.pk))
                    start_time = talk.talkslot.time.start_time
                    duration = talk.talkslot.time.end_time - start_time
                    ET.SubElement(event_xml, 'date').text = self.to_xml_timestamp(start_time, context)
                    ET.SubElement(event_xml, 'start').text = self.to_xml_localtime(start_time, context)
                    ET.SubElement(event_xml, 'duration').text = "%02d:%02d" % (
                        duration.seconds / 3600, duration.seconds % 3600 / 60)
                    ET.SubElement(event_xml, 'room').text = room.name
                    ET.SubElement(event_xml, 'title').text = talk.title
                    ET.SubElement(event_xml, 'abstract').text = talk.abstract
                    ET.SubElement(event_xml, 'language').text = 'de'
                    persons_xml = ET.SubElement(event_xml, 'persons')
                    ET.SubElement(persons_xml, 'person', id=str(talk.speaker_id)).text = \
                        talk.speaker.user.user.get_full_name()

        response_kwargs.setdefault('content_type', 'application/xml')
        return HttpResponse(content=ET.tostring(schedule_xml, 'utf-8'), **response_kwargs)


class CommitteeTalkDetails(CommitteeRequiredMixin, DetailView):
    model = Talk
    template_name_suffix = '_committee_details'

    def get_queryset(self):
        return super(CommitteeTalkDetails, self).get_queryset().select_related(
            'speaker', 'speaker__user', 'speaker__user__user'
        ).annotate(
            average_score=Avg('vote__score')
        )

    def get_context_data(self, **kwargs):
        context = super(CommitteeTalkDetails, self).get_context_data(**kwargs)
        talk = context['talk']
        try:
            user_vote = talk.vote_set.get(voter=self.request.user)
            user_score = user_vote.score
        except Vote.DoesNotExist:
            user_score = None
        context.update({
            'comment_form': TalkCommentForm(instance=talk),
            'user_vote': user_score,
            'average_votes': talk.average_score,
            'comments': talk.talkcomment_set.select_related('commenter').order_by('-modified').all()
        })
        return context


class CommitteeSubmitTalkComment(CommitteeRequiredMixin, SingleObjectMixin, FormView):
    model = Talk
    form_class = TalkCommentForm
    http_method_names = ['post']
    email_subject_template = 'talk/talk_comment_email_subject.txt'
    email_body_template = 'talk/talk_comment_email_body.txt'
    talk_comment = None

    def get_email_context(self):
        return {
            'talk': self.get_object(),
            'request': self.request,
            'comment': self.talk_comment,
            'site': get_current_site(self.request),
            'event': 'Dev Day 2017'
        }

    def get_email_subject(self):
        return render_to_string(self.email_subject_template, self.get_email_context())

    def get_email_text_body(self):
        return render_to_string(self.email_body_template, self.get_email_context())

    def form_invalid(self, form):
        messages.warning(self.request, form.errors)
        # TODO: implement form_invalid for ajax calls
        return redirect(self.get_success_url())

    def form_valid(self, form):
        # TODO: implement form valid for ajax calls
        talk = self.get_object()
        self.talk_comment = talk.talkcomment_set.create(
            commenter=self.request.user, comment=form.cleaned_data['comment'],
            is_visible=form.cleaned_data['is_visible'])

        # send email to speaker if comment is visible
        if self.talk_comment.is_visible:
            recipient = talk.speaker.user.user.email
            send_mail(
                self.get_email_subject(),
                self.get_email_text_body(),
                settings.DEFAULT_FROM_EMAIL,
                [recipient])
        return super(CommitteeSubmitTalkComment, self).form_valid(form)

    def get_success_url(self):
        talk = self.get_object()
        return reverse_lazy('talk_details', kwargs={'pk': talk.pk})

    def get_form_kwargs(self):
        kwargs = super(CommitteeSubmitTalkComment, self).get_form_kwargs()
        kwargs['instance'] = self.get_object()
        return kwargs


class CommitteeTalkVote(CommitteeRequiredMixin, UpdateView):
    model = Talk
    http_method_names = ['post']
    form_class = TalkVoteForm

    def form_invalid(self, form):
        return JsonResponse({'message': 'error', 'errors': form.errors})

    def form_valid(self, form):
        talk = self.get_object()
        score = form.cleaned_data['score']
        try:
            vote = talk.vote_set.get(voter=self.request.user)
            vote.score = score
            vote.save()
        except Vote.DoesNotExist:
            talk.vote_set.create(voter=self.request.user, score=score)
        return JsonResponse({'message': 'ok'})


class CommitteeTalkVoteClear(CommitteeRequiredMixin, SingleObjectMixin, View):
    model = Talk
    http_method_names = ['post']

    # noinspection PyUnusedLocal
    def post(self, request, *args, **kwargs):
        talk = self.get_object()
        talk.vote_set.filter(voter=request.user).delete()
        return JsonResponse({'message': 'vote deleted'})


class CommitteeTalkCommentDelete(CommitteeRequiredMixin, SingleObjectMixin, View):
    model = TalkComment
    http_method_names = ['post']

    def get_queryset(self):
        return super(CommitteeTalkCommentDelete, self).get_queryset().filter(commenter=self.request.user)

    # noinspection PyUnusedLocal
    def post(self, request, *args, **kwargs):
        self.get_object().delete()
        return JsonResponse({'message': 'comment deleted'})


class SpeakerTalkDetails(SpeakerRequiredMixin, UpdateView):
    model = Talk
    template_name_suffix = '_speaker_details'
    form_class = EditTalkForm

    def get_success_url(self):
        return reverse('speaker_talk_details', kwargs={'pk': self.object.pk})

    def get_queryset(self):
        return super(SpeakerTalkDetails, self).get_queryset().select_related('speaker').filter(
            speaker__user__user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(SpeakerTalkDetails, self).get_context_data(**kwargs)
        context['comments'] = context['talk'].talkcomment_set.filter(is_visible=True).all()
        context['comment_form'] = TalkSpeakerCommentForm(instance=context['talk'])
        return context


class SubmitTalkSpeakerComment(SpeakerRequiredMixin, SingleObjectMixin, FormView):
    model = Talk
    form_class = TalkSpeakerCommentForm
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
            is_visible=True)
        return super(SubmitTalkSpeakerComment, self).form_valid(form)

    def get_success_url(self):
        talk = self.get_object()
        return reverse_lazy('speaker_talk_details', kwargs={'pk': talk.pk})

    def get_form_kwargs(self):
        kwargs = super(SubmitTalkSpeakerComment, self).get_form_kwargs()
        kwargs['instance'] = self.get_object()
        return kwargs

    def get_queryset(self):
        return super(SubmitTalkSpeakerComment, self).get_queryset().filter(speaker__user__user=self.request.user)


class TalkSpeakerCommentDelete(SpeakerRequiredMixin, SingleObjectMixin, View):
    model = TalkComment
    http_method_names = ['post']

    def get_queryset(self):
        return super(TalkSpeakerCommentDelete, self).get_queryset().filter(commenter=self.request.user)

    # noinspection PyUnusedLocal
    def post(self, request, *args, **kwargs):
        self.get_object().delete()
        return JsonResponse({'message': 'comment deleted'})


class SpeakerListView(ListView):
    model = Speaker

    def get_queryset(self):
        return super(SpeakerListView, self).get_queryset().filter(talk__track__isnull=False).order_by(
            'user__user__last_name', 'user__user__first_name').prefetch_related('user', 'user__user')


class RedirectVideoView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse('video_list', kwargs={'event': get_object_or_404(Event, pk=settings.EVENT_ID).slug})
