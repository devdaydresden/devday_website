import csv
import logging
import xml.etree.ElementTree as ElementTree
from datetime import date, timedelta
from io import StringIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import AccessMixin, PermissionRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core import signing
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Avg, Count, Max, Min, Prefetch, Sum
from django.db.transaction import atomic
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, RedirectView, TemplateView, View
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.edit import (
    BaseFormView,
    CreateView,
    DeleteView,
    FormView,
    ModelFormMixin,
    UpdateView,
)
from django.views.generic.list import BaseListView

from attendee.forms import DevDayRegistrationForm
from attendee.models import Attendee
from attendee.views import AttendeeRequiredMixin, StaffUserMixin
from event.models import Event
from speaker.models import Speaker
from talk import signals
from talk.forms import (
    AttendeeTalkFeedbackForm,
    AttendeeTalkVoteForm,
    CreateTalkForm,
    EditTalkForm,
    TalkAddReservationForm,
    TalkCommentForm,
    TalkSpeakerCommentForm,
    TalkVoteForm,
)
from talk.models import (
    AttendeeFeedback,
    AttendeeVote,
    Room,
    SessionReservation,
    Talk,
    TalkComment,
    TalkSlot,
    TimeSlot,
    Vote,
)
from talk.reservation import get_reservation_email_context

logger = logging.getLogger("talk")

User = get_user_model()

XML_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


class PrepareSubmitSessionView(FormView):
    """
    This view is used to inform a potential speaker about the registration
    process.
    """

    template_name = "talk/prepare_submit_session.html"
    form_class = DevDayRegistrationForm

    def get(self, request, *args, **kwargs):
        if request.user.is_anonymous:
            return super(PrepareSubmitSessionView, self).get(request, *args, **kwargs)
        try:
            _ = request.user.speaker
            return redirect(
                reverse("create_session", kwargs={"event": self.kwargs.get("event")})
            )
        except ObjectDoesNotExist:
            return redirect(
                "{}?next={}".format(
                    reverse("create_speaker"),
                    reverse(
                        "create_session", kwargs={"event": self.kwargs.get("event")}
                    ),
                )
            )


class TalkSubmissionOpenMixin(object):
    def dispatch(self, request, *args, **kwargs):
        event = get_object_or_404(Event, slug=kwargs.get("event", ""))
        if not event.submission_open:
            return redirect("talk_submission_closed")
        # noinspection PyUnresolvedReferences
        return super(TalkSubmissionOpenMixin, self).dispatch(request, *args, **kwargs)


class TalkSubmissionClosed(TemplateView):
    template_name = "talk/submission_closed.html"


class SpeakerRequiredMixin(AccessMixin):
    speaker = None

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return self.handle_no_permission()
        try:
            self.speaker = user.speaker
        except ObjectDoesNotExist:
            return redirect(
                "{}?next={}".format(reverse("create_speaker"), request.path)
            )
        # noinspection PyUnresolvedReferences
        return super(SpeakerRequiredMixin, self).dispatch(request, *args, **kwargs)


class TalkSubmittedView(SpeakerRequiredMixin, TemplateView):
    template_name = "talk/submitted.html"

    def get_context_data(self, **kwargs):
        context = super(TalkSubmittedView, self).get_context_data(**kwargs)
        context["event"] = Event.objects.get(slug=self.kwargs.get("event"))
        context["speaker"] = self.request.user.speaker
        return context


class CreateTalkView(TalkSubmissionOpenMixin, SpeakerRequiredMixin, CreateView):
    model = Talk
    form_class = CreateTalkForm
    event = None

    def get_success_url(self):
        return reverse_lazy("talk_submitted", kwargs={"event": self.event.slug})

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, slug=self.kwargs.get("event"))
        return super(CreateTalkView, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial.update({"draft_speaker": self.speaker, "event": self.event})
        return initial

    def get_context_data(self, **kwargs):
        context = super(CreateTalkView, self).get_context_data(**kwargs)
        context["event"] = self.event
        return context


class CommitteeRequiredMixin(PermissionRequiredMixin):
    permission_required = ("talk.add_vote", "talk.add_talkcomment")


class TalkDetails(DetailView):
    model = Talk
    slug_url_kwarg = "slug"
    slug_field = "slug"
    template_name_suffix = "_details"
    event = None

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, slug=self.kwargs["event"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            super(TalkDetails, self)
            .get_queryset()
            .filter(event=self.event)
            .prefetch_related("media", "published_speaker")
        )

    def get_context_data(self, **kwargs):
        context = super(TalkDetails, self).get_context_data(**kwargs)
        current = self.event == Event.objects.current_event()
        context.update(
            {
                "speaker": context["talk"].published_speaker,
                "event": self.event,
                "current": current,
            }
        )
        if self.request.user.is_authenticated:
            attendee = Attendee.objects.filter(
                event=self.event, user=self.request.user
            ).first()
            if attendee is not None:
                talk = context["talk"]
                context["reservation"] = SessionReservation.objects.filter(
                    talk=talk, attendee=attendee
                ).first()
                if talk.is_feedback_allowed or self.request.user.is_staff:
                    existing_feedback = AttendeeFeedback.objects.filter(
                        talk=talk, attendee=attendee
                    ).first()
                    context["feedback_form"] = AttendeeTalkFeedbackForm(
                        instance=existing_feedback, attendee=attendee, talk=talk
                    )
        return context


class CommitteeTalkOverview(CommitteeRequiredMixin, ListView):
    model = Talk
    template_name_suffix = "_committee_overview"

    ORDER_MAP = {
        "speaker": "draft_speaker__name",
        "score": "average_score",
        "score_sum": "vote_sum",
    }

    def get_queryset(self):
        qs = (
            super(CommitteeTalkOverview, self)
            .get_queryset()
            .filter(event=Event.objects.current_event())
            .annotate(
                average_score=Avg("vote__score"),
                vote_sum=Sum("vote__score"),
                vote_count=Count("vote__id"),
            )
            .select_related("draft_speaker", "draft_speaker__user")
            .order_by("title")
        )
        sort_order = self.request.GET.get("sort_order", "title")
        sort_order = CommitteeTalkOverview.ORDER_MAP.get(sort_order, sort_order)
        if self.request.GET.get("sort_dir") == "desc":
            sort_order = "-{}".format(sort_order)
        return qs.order_by(sort_order)

    def get_context_data(self, **kwargs):
        context = super(CommitteeTalkOverview, self).get_context_data(**kwargs)
        talk_list = context["talk_list"]
        for item in (
            Talk.objects.values("id")
            .annotate(comment_count=Count("talkcomment__id"))
            .all()
        ):
            for talk in talk_list:
                if item["id"] == talk.id:
                    setattr(talk, "comment_count", item["comment_count"])
        context.update(
            {
                "sort_order": self.request.GET.get("sort_order", "title"),
                "sort_dir": self.request.GET.get("sort_dir", "asc"),
            }
        )
        return context


class CommitteeSpeakerDetails(CommitteeRequiredMixin, DetailView):
    model = Speaker
    template_name = "talk/speaker_details.html"


class TalkListView(ListView):
    model = Talk

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, slug=self.kwargs.get("event"))
        if (
            self.event.published and self.event.sessions_published
        ) or request.user.is_staff:
            return super(TalkListView, self).dispatch(request, *args, **kwargs)
        raise Http404

    def get_queryset(self):
        qs = (
            super(TalkListView, self)
            .get_queryset()
            .filter(track__isnull=False, event=self.event)
            .select_related(
                "track",
                "published_speaker",
                "event",
                "talkslot",
                "talkslot__time",
                "talkslot__room",
            )
        )
        return qs.order_by("title")

    def get_context_data_for_grid(self, context, **kwargs):
        all_talks = context.get("talk_list", [])
        time_slots = list(
            TimeSlot.objects.filter(event=self.event).order_by(
                "block", "start_time", "end_time"
            )
        )
        talk_slots = list(
            TalkSlot.objects.filter(talk__event=self.event)
            .select_related(
                "talk",
                "room",
                "time",
                "talk__event",
                "talk__published_speaker",
                "talk__published_speaker__event",
            )
            .order_by("time__start_time")
        )

        rooms = list(Room.objects.for_event(self.event))

        blocks = {}

        # assign time slots to blocks
        for time_slot in time_slots:
            block = blocks.setdefault(
                time_slot.block, {"time_slots": [], "rooms": set()}
            )
            time_talk_slots = [
                (talk_slot.room_id, talk_slot.talk)
                for talk_slot in talk_slots
                if talk_slot.time_id == time_slot.id
            ]
            block["time_slots"].append((time_slot, time_talk_slots, []))
            block["rooms"] |= {
                talk_slot_tuple[0] for talk_slot_tuple in time_talk_slots
            }

        # sort talks into ordered rooms
        for block in blocks.values():
            block["rooms"] = [room for room in rooms if room.id in block["rooms"]]
            grouped_talks = {}
            for time_slot, time_talk_slots, overlaps in block["time_slots"]:
                grouped_talks.setdefault(
                    time_slot, {"room_talks": {}, "attributes": {}}
                )
                for room_id, talk in time_talk_slots:
                    room_talks = grouped_talks[time_slot]["room_talks"]
                    for room in block["rooms"]:
                        if room.id == room_id:
                            room_talks.setdefault(room, []).append(talk)

            # calculate overlaps
            time_slot_count = len(block["time_slots"])
            for index1 in range(time_slot_count):
                time_slot1, time_talk_slots1, overlaps1 = block["time_slots"][index1]
                for index2 in range(time_slot_count):
                    time_slot2, time_talk_slots2, overlaps2 = block["time_slots"][
                        index2
                    ]
                    if (
                        time_slot1 != time_slot2
                        and time_slot1.start_time >= time_slot2.start_time
                        and time_slot1.end_time <= time_slot2.end_time
                    ):
                        overlaps2.append(index1)
                        overlaps1.append(index2)

            schedule = []
            scheduled_times = {}
            row = 0

            # calculate column and row spans
            for time_slot, time_talk_slots, overlaps in block["time_slots"]:
                attributes = grouped_talks[time_slot]["attributes"]
                if len(overlaps) > 1:
                    attributes["rowspan"] = len(overlaps)
                elif len(overlaps) == 1:
                    attributes["colspan"] = len(block["rooms"]) - 1
                if time_slot.start_time not in scheduled_times:
                    scheduled_times[time_slot.start_time] = row
                    index = row
                    row += 1
                else:
                    index = scheduled_times[time_slot.start_time]
                if len(schedule) - 1 < index:
                    schedule_row = {
                        "time_slots": [[time_slot, attributes]],
                        "room_talks": {},
                    }
                    schedule.append(schedule_row)
                else:
                    schedule[index]["time_slots"].append([time_slot, attributes])
                for room in block["rooms"]:
                    if room in grouped_talks[time_slot]["room_talks"]:
                        schedule[index]["room_talks"].setdefault(room, []).extend(
                            [
                                time_slot,
                                grouped_talks[time_slot]["room_talks"][room],
                                attributes,
                            ]
                        )
                block["schedule"] = schedule

        unscheduled = []
        for talk in all_talks:
            try:
                talk.talkslot.time
            except TalkSlot.DoesNotExist:
                unscheduled.append(talk)
        context.update(
            {"event": self.event, "unscheduled": unscheduled, "blocks": blocks}
        )
        if (
            self.request.user.is_authenticated
            and Attendee.objects.filter(
                event=self.event, user=self.request.user
            ).exists()
        ):
            context["reservations"] = {
                r.talk: r
                for r in list(
                    SessionReservation.objects.filter(
                        talk__event=self.event, attendee__user=self.request.user
                    ).only("talk")
                )
            }
        return context

    def get_context_data_for_list(self, context, **kwargs):
        context.update({"event": self.event})
        return context

    def get_context_data(self, **kwargs):
        context = super(TalkListView, self).get_context_data(**kwargs)
        if self.event == Event.objects.current_event():
            return self.get_context_data_for_grid(context, **kwargs)
        return self.get_context_data_for_list(context, **kwargs)

    def get_template_names(self):
        if self.event == Event.objects.current_event():
            return "talk/talk_grid.html"
        return "talk/talk_list.html"


class TalkListPreviewView(ListView):
    model = Talk
    template_name_suffix = "_list_preview"

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, slug=self.kwargs.get("event"))
        return super(TalkListPreviewView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            super(TalkListPreviewView, self)
            .get_queryset()
            .filter(track__isnull=False, event=self.event)
            .select_related("event", "track", "published_speaker")
            .order_by("title")
        )

    def get_context_data(self, **kwargs):
        context = super(TalkListPreviewView, self).get_context_data(**kwargs)
        context["event"] = self.event
        return context


class TalkVideoView(ListView):
    model = Talk
    template_name_suffix = "_videos"
    event = None

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, slug=self.kwargs.get("event"))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            super(TalkVideoView, self)
            .get_queryset()
            .filter(event=self.event, track__isnull=False, media__isnull=False)
            .select_related("published_speaker", "media")
            .order_by("title")
        )

    def get_context_data(self, **kwargs):
        context = super(TalkVideoView, self).get_context_data(**kwargs)
        context["event"] = self.event
        return context


class InfoBeamerXMLView(BaseListView):
    model = Talk

    def dispatch(self, request, *args, **kwargs):
        event = self.kwargs.get("event")
        if not event:
            return HttpResponseRedirect(
                "/{}/schedule.xml".format(Event.objects.current_event().slug)
            )
        return super(InfoBeamerXMLView, self).dispatch(request, *args, **kwargs)

    def recalculate_timestamp(self, timestamp, context):
        if "starttoday" in self.request.GET:
            start_time = context.get("min_time")
            delta = date.today() - start_time.date()
        else:
            delta = timedelta()
        delta += timedelta(hours=int(self.request.GET.get("offsethours", "0")))
        local_time = timezone.localtime(
            timestamp + delta, timezone.get_default_timezone()
        )
        return local_time

    def to_xml_timestamp(self, timestamp, context):
        formatted = self.recalculate_timestamp(timestamp, context).strftime(
            XML_TIMESTAMP_FORMAT
        )
        return "%s:%s" % (formatted[:-2], formatted[-2:])

    def to_xml_localtime(self, timestamp, context):
        return self.recalculate_timestamp(timestamp, context).strftime("%H:%M")

    def to_xml_date(self, timestamp, context):
        return self.recalculate_timestamp(timestamp, context).strftime("%Y-%m-%d")

    def get_queryset(self):
        event = get_object_or_404(Event, slug=self.kwargs.get("event"))
        return (
            super(InfoBeamerXMLView, self)
            .get_queryset()
            .filter(track__isnull=False, event=event, talkslot__time__event=event)
            .select_related(
                "track",
                "published_speaker",
                "talkslot",
                "talkslot__time",
                "talkslot__room",
            )
            .order_by("talkslot__time__start_time", "talkslot__room__name")
        )

    def get_context_data(self, **kwargs):
        context = super(InfoBeamerXMLView, self).get_context_data(**kwargs)
        event = get_object_or_404(Event, slug=self.kwargs.get("event"))
        time_slots = TimeSlot.objects.filter(event=event)
        if not time_slots.exists():
            raise Http404()
        time_range = time_slots.aggregate(Min("start_time"), Max("end_time"))
        context["min_time"] = time_range["start_time__min"]
        context["max_time"] = time_range["end_time__max"]
        talks = context.get("talk_list", [])
        talks_by_room_and_time = {}
        for talk in talks:
            # build dictionary grouped by room and time (sm and xs display)
            talks_by_room_and_time.setdefault(talk.talkslot.room, []).append(talk)
        context.update(
            {
                "event": event,
                "talks_by_room_and_time": talks_by_room_and_time,
                "rooms": event.room_set.all(),
                "times": time_slots,
            }
        )
        return context

    def render_to_response(self, context, **response_kwargs):
        event = context.get("event")
        schedule_xml = ElementTree.Element("schedule")
        # TODO: use event argument and render proper event title
        ElementTree.SubElement(schedule_xml, "version").text = event.title
        conference = ElementTree.SubElement(schedule_xml, "conference")
        ElementTree.SubElement(conference, "acronym").text = "DevDay"
        ElementTree.SubElement(conference, "title").text = event.title
        ElementTree.SubElement(conference, "start").text = self.to_xml_date(
            event.start_time, context
        )
        ElementTree.SubElement(conference, "end").text = self.to_xml_date(
            event.end_time, context
        )
        ElementTree.SubElement(conference, "days").text = "1"  # FIXME compute days
        ElementTree.SubElement(conference, "timeslot_duration").text = "00:15"
        day_xml = ElementTree.SubElement(
            schedule_xml,
            "day",
            index="1",
            date=self.to_xml_date(context["min_time"], context),
            start=self.to_xml_timestamp(context["min_time"], context),
            end=self.to_xml_timestamp(context["max_time"], context),
        )
        room_talks = context["talks_by_room_and_time"]
        for room in room_talks:
            room_xml = ElementTree.SubElement(day_xml, "room", name=room.name)
            for talk in room_talks[room]:
                event_xml = ElementTree.SubElement(
                    room_xml, "event", guid=str(talk.pk), id=str(talk.pk)
                )
                start_time = talk.talkslot.time.start_time
                duration = talk.talkslot.time.end_time - start_time
                ElementTree.SubElement(event_xml, "date").text = self.to_xml_timestamp(
                    start_time, context
                )
                ElementTree.SubElement(event_xml, "start").text = self.to_xml_localtime(
                    start_time, context
                )
                ElementTree.SubElement(event_xml, "duration").text = "%02d:%02d" % (
                    duration.seconds / 3600,
                    duration.seconds % 3600 / 60,
                )
                ElementTree.SubElement(event_xml, "room").text = room.name
                ElementTree.SubElement(event_xml, "title").text = talk.title
                ElementTree.SubElement(event_xml, "abstract").text = talk.abstract
                ElementTree.SubElement(event_xml, "language").text = "de"
                persons_xml = ElementTree.SubElement(event_xml, "persons")
                ElementTree.SubElement(
                    persons_xml, "person", id=str(talk.published_speaker_id)
                ).text = talk.published_speaker.name

        response_kwargs.setdefault("content_type", "application/xml")
        return HttpResponse(
            content=ElementTree.tostring(schedule_xml, "utf-8"), **response_kwargs
        )


class CommitteeTalkDetails(CommitteeRequiredMixin, DetailView):
    model = Talk
    template_name_suffix = "_committee_details"

    def get_queryset(self):
        return (
            super(CommitteeTalkDetails, self)
            .get_queryset()
            .select_related("draft_speaker", "draft_speaker__user")
            .annotate(average_score=Avg("vote__score"))
        )

    def get_context_data(self, **kwargs):
        context = super(CommitteeTalkDetails, self).get_context_data(**kwargs)
        talk = context["talk"]
        try:
            user_vote = talk.vote_set.get(voter=self.request.user)
            user_score = user_vote.score
        except Vote.DoesNotExist:
            user_score = None
        context.update(
            {
                "comment_form": TalkCommentForm(instance=talk),
                "user_vote": user_score,
                "average_votes": talk.average_score,
                "comments": talk.talkcomment_set.select_related("commenter")
                .order_by("-modified")
                .all(),
            }
        )
        return context


class CommitteeSubmitTalkComment(CommitteeRequiredMixin, SingleObjectMixin, FormView):
    model = Talk
    form_class = TalkCommentForm
    http_method_names = ["post"]
    email_subject_template = "talk/talk_comment_email_subject.txt"
    email_body_template = "talk/talk_comment_email_body.txt"
    talk_comment = None

    def get_email_context(self):
        return {
            "talk": self.get_object(),
            "request": self.request,
            "comment": self.talk_comment,
            "site": get_current_site(self.request),
            "event": "Dev Day 2017",
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
            commenter=self.request.user,
            comment=form.cleaned_data["comment"],
            is_visible=form.cleaned_data["is_visible"],
        )

        # send email to speaker if comment is visible
        if self.talk_comment.is_visible:
            recipient = talk.draft_speaker.user.email
            send_mail(
                self.get_email_subject(),
                self.get_email_text_body(),
                settings.DEFAULT_FROM_EMAIL,
                [recipient],
            )
        return super(CommitteeSubmitTalkComment, self).form_valid(form)

    def get_success_url(self):
        talk = self.get_object()
        return reverse_lazy("talk_committee_details", kwargs={"pk": talk.pk})

    def get_form_kwargs(self):
        kwargs = super(CommitteeSubmitTalkComment, self).get_form_kwargs()
        kwargs["instance"] = self.get_object()
        return kwargs


class CommitteeTalkVote(CommitteeRequiredMixin, UpdateView):
    model = Talk
    http_method_names = ["post"]
    form_class = TalkVoteForm

    def form_invalid(self, form):
        return JsonResponse({"message": "error", "errors": form.errors})

    def form_valid(self, form):
        talk = self.get_object()
        score = form.cleaned_data["score"]
        try:
            vote = talk.vote_set.get(voter=self.request.user)
            vote.score = score
            vote.save()
        except Vote.DoesNotExist:
            talk.vote_set.create(voter=self.request.user, score=score)
        return JsonResponse({"message": "ok"})


class CommitteeTalkVoteClear(CommitteeRequiredMixin, SingleObjectMixin, View):
    model = Talk
    http_method_names = ["post"]

    # noinspection PyUnusedLocal
    def post(self, request, *args, **kwargs):
        talk = self.get_object()
        talk.vote_set.filter(voter=request.user).delete()
        return JsonResponse({"message": "vote deleted"})


class CommitteeTalkCommentDelete(CommitteeRequiredMixin, SingleObjectMixin, View):
    model = TalkComment
    http_method_names = ["post"]

    def get_queryset(self):
        return (
            super(CommitteeTalkCommentDelete, self)
            .get_queryset()
            .filter(commenter=self.request.user)
        )

    # noinspection PyUnusedLocal
    def post(self, request, *args, **kwargs):
        self.get_object().delete()
        return JsonResponse({"message": "comment deleted"})


class SpeakerTalkDetails(SpeakerRequiredMixin, UpdateView):
    model = Talk
    template_name_suffix = "_speaker_details"
    form_class = EditTalkForm

    def get_success_url(self):
        return reverse("speaker_talk_details", kwargs={"pk": self.object.pk})

    def get_queryset(self):
        return (
            super(SpeakerTalkDetails, self)
            .get_queryset()
            .select_related("draft_speaker")
            .filter(draft_speaker__user=self.request.user)
        )

    def get_context_data(self, **kwargs):
        context = super(SpeakerTalkDetails, self).get_context_data(**kwargs)
        context["comments"] = (
            context["talk"].talkcomment_set.filter(is_visible=True).all()
        )
        context["comment_form"] = TalkSpeakerCommentForm(instance=context["talk"])
        return context


class SubmitTalkSpeakerComment(SpeakerRequiredMixin, SingleObjectMixin, FormView):
    model = Talk
    form_class = TalkSpeakerCommentForm
    http_method_names = ["post"]

    def form_invalid(self, form):
        messages.warning(self.request, form.errors)
        # TODO: implement form_invalid for ajax calls
        return redirect(self.get_success_url())

    def form_valid(self, form):
        # TODO: implement form valid for ajax calls
        talk = self.get_object()
        talk.talkcomment_set.create(
            commenter=self.request.user,
            comment=form.cleaned_data["comment"],
            is_visible=True,
        )
        return super(SubmitTalkSpeakerComment, self).form_valid(form)

    def get_success_url(self):
        talk = self.get_object()
        return reverse_lazy("speaker_talk_details", kwargs={"pk": talk.pk})

    def get_form_kwargs(self):
        kwargs = super(SubmitTalkSpeakerComment, self).get_form_kwargs()
        kwargs["instance"] = self.get_object()
        return kwargs

    def get_queryset(self):
        return (
            super(SubmitTalkSpeakerComment, self)
            .get_queryset()
            .filter(draft_speaker__user=self.request.user)
        )


class TalkSpeakerCommentDelete(SpeakerRequiredMixin, SingleObjectMixin, View):
    model = TalkComment
    http_method_names = ["post"]

    def get_queryset(self):
        return (
            super(TalkSpeakerCommentDelete, self)
            .get_queryset()
            .filter(commenter=self.request.user)
        )

    # noinspection PyUnusedLocal
    def post(self, request, *args, **kwargs):
        self.get_object().delete()
        return JsonResponse({"message": "comment deleted"})


class RedirectVideoView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse(
            "video_list", kwargs={"event": Event.objects.current_event().slug}
        )


class EventSessionSummaryView(StaffUserMixin, BaseListView):
    model = Talk

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(event=Event.objects.current_event())
            .select_related("draft_speaker")
            .order_by("title")
        )

    def render_to_response(self, context):
        output = StringIO()
        try:
            writer = csv.writer(output, delimiter=";")
            writer.writerow(
                (
                    "Speaker",
                    "Organization",
                    "Title",
                    "Abstract",
                    "Remarks",
                    "Formats",
                    "Avg. Score",
                    "Total Score",
                    "Comments",
                )
            )
            writer.writerows(
                [
                    [
                        t.draft_speaker.name,
                        t.draft_speaker.organization,
                        t.title,
                        t.abstract,
                        t.remarks,
                        ", ".join([str(f) for f in t.talkformat.all()]),
                        t.vote_set.aggregate(Avg("score"))["score__avg"],
                        t.vote_set.aggregate(Sum("score"))["score__sum"],
                        "\n".join(
                            [
                                "%s: %s (%s)" % (c.commenter, c.comment, c.modified)
                                for c in t.talkcomment_set.order_by("modified").all()
                            ]
                        ),
                    ]
                    for t in context.get("object_list", [])
                ]
            )
            response = HttpResponse(
                output.getvalue(), content_type="txt/csv; charset=utf-8"
            )
            response["Content-Disposition"] = "attachment; filename=session-summary.csv"
            return response
        finally:
            output.close()


class AttendeeVotingView(AttendeeRequiredMixin, ListView):
    model = Talk
    template_name_suffix = "_voting"

    def get(self, request, *args, **kwargs):
        if not self.event.voting_open:
            raise Http404()
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .filter(track__isnull=False, event=self.event)
            .select_related("track", "published_speaker")
            .prefetch_related()
        )
        if self.request.user.is_staff:
            qs = qs.annotate(
                vote_count=Count("attendeevote"),
                vote_average=Avg("attendeevote__score"),
            )
        return qs.order_by("title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event"] = self.event
        attendee_scores = self.attendee.attendeevote_set.all()
        scores = {talk.pk: 0 for talk in context["talk_list"]}
        for score in attendee_scores:
            scores[score.talk_id] = score.score
        for talk in context["talk_list"]:
            setattr(talk, "score", scores[talk.id])
        return context


class AttendeeTalkVote(AttendeeRequiredMixin, BaseFormView):
    model = Talk
    http_method_names = ["post"]
    form_class = AttendeeTalkVoteForm
    talk = None

    def post(self, request, *args, **kwargs):
        if not self.event.voting_open:
            raise Http404()
        if "talk-id" not in self.request.POST:
            return HttpResponseBadRequest()
        self.talk = get_object_or_404(
            Talk,
            id=self.request.POST.get("talk-id", -1),
            event=self.event,
            track__isnull=False,
        )
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        return JsonResponse({"message": "error", "errors": form.errors})

    def form_valid(self, form):
        score = form.cleaned_data["score"]
        AttendeeVote.objects.upsert(
            conflict_target=["attendee", "talk"],
            fields={"attendee": self.attendee, "score": score, "talk": self.talk},
        )
        return JsonResponse({"message": "ok"})


class AttendeeTalkClearVote(AttendeeRequiredMixin, View):
    model = Talk
    http_method_names = ["post"]

    @atomic
    def post(self, request, *args, **kwargs):
        if not self.event.voting_open:
            raise Http404()
        if "talk-id" not in self.request.POST:
            return HttpResponseBadRequest()
        talk = get_object_or_404(
            Talk,
            id=request.POST.get("talk-id", -1),
            event=self.event,
            track__isnull=False,
        )
        talk.attendeevote_set.filter(attendee=self.attendee).delete()
        return JsonResponse({"message": "vote deleted"})


class ReservationConfirmationViewMixin(object):
    email_subject_template = "talk/sessionreservation_confirm_subject.txt"
    email_body_template = "talk/sessionreservation_confirm_body.txt"

    talk = None
    attendee = None
    request = None

    def get_success_url(self, reservation=None):
        if reservation and reservation.is_waiting:
            pattern_name = "talk_reservation_waiting"
        else:
            pattern_name = "talk_reservation_confirmation_sent"
        return reverse(
            pattern_name, kwargs={"event": self.talk.event.slug, "slug": self.talk.slug}
        )

    def send_confirmation_mail(self, reservation):
        user = reservation.attendee.user
        confirmation_key = reservation.get_confirmation_key()
        context = get_reservation_email_context(
            reservation, self.request, confirmation_key
        )
        subject = render_to_string(
            template_name=self.email_subject_template,
            context=context,
            request=self.request,
        )
        # Force subject to a single line to avoid header-injection
        # issues.
        subject = "".join(subject.splitlines())
        message = render_to_string(
            template_name=self.email_body_template,
            context=context,
            request=self.request,
        )
        user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)


class TalkAddReservation(
    AttendeeRequiredMixin, ReservationConfirmationViewMixin, CreateView
):
    model = SessionReservation
    template_name_suffix = "_create"
    form_class = TalkAddReservationForm

    def check_reservation(self):
        return SessionReservation.objects.filter(
            talk=self.talk, attendee=self.attendee
        ).first()

    def get(self, request, *args, **kwargs):
        self.get_talk_and_attendee(**kwargs)
        reservation = self.check_reservation()
        if reservation:
            return redirect(self.get_success_url(reservation=reservation))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.get_talk_and_attendee(**kwargs)
        reservation = self.check_reservation()
        if reservation:
            return redirect(self.get_success_url(reservation=reservation))
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"attendee": self.attendee, "talk": self.talk})
        return kwargs

    def get_talk_and_attendee(self, **kwargs):
        self.talk = get_object_or_404(
            Talk, event=self.event, slug=kwargs["slug"], spots__gt=0
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "talk": self.talk,
                "event": self.talk.event,
                "fully_booked": self.talk.sessionreservation_set.filter(
                    is_confirmed=True
                ).count()
                >= self.talk.spots,
            }
        )
        return context

    def form_valid(self, form):
        reservation = form.save(commit=True)
        if not reservation.is_waiting:
            self.send_confirmation_mail(reservation)
        return HttpResponseRedirect(self.get_success_url(reservation=reservation))


class TalkResendReservationConfirmation(
    AttendeeRequiredMixin, ReservationConfirmationViewMixin, UpdateView
):
    model = SessionReservation
    fields = []
    success_url = "talk_confirmation_sent"
    template_name_suffix = "_resend_confirmation"
    object = None

    def get_talk_and_attendee(self, request, **kwargs):
        self.talk = get_object_or_404(
            Talk, event__slug=kwargs["event"], slug=kwargs["slug"]
        )

    def get_object(self, queryset=None):
        self.get_talk_and_attendee(self.request, **self.kwargs)
        return get_object_or_404(
            SessionReservation, talk=self.talk, attendee=self.attendee
        )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.is_confirmed or self.object.is_waiting:
            return HttpResponseBadRequest()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.is_confirmed or self.object.is_waiting:
            return HttpResponseBadRequest()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        self.send_confirmation_mail(self.object)
        return HttpResponseRedirect(self.get_success_url())


class TalkReservationConfirmationSent(AttendeeRequiredMixin, TemplateView):
    template_name = "talk/sessionreservation_confirmation_sent.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {"talk": Talk.objects.get(slug=kwargs["slug"], event=self.event)}
        )
        return context


class TalkCancelReservation(AttendeeRequiredMixin, DeleteView):
    model = SessionReservation
    template_name_suffix = "_confirm_cancel"
    object = None

    def get_object(self, queryset=None):
        return get_object_or_404(
            SessionReservation,
            attendee__user=self.request.user,
            talk__event=self.event,
            talk__slug=self.kwargs["slug"],
        )

    def get_success_url(self):
        return reverse(
            "talk_details",
            kwargs={"event": self.event.slug, "slug": self.kwargs["slug"]},
        )

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        signals.session_reservation_cancelled.send(
            sender=self.__class__, reservation=self.object, request=self.request
        )
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)


class ConfirmationError(Exception):
    def __init__(self, message, code=None, params=None):
        super().__init__(message, code, params)
        self.message = message
        self.code = code
        self.params = params


class TalkConfirmReservation(AttendeeRequiredMixin, TemplateView):
    EXPIRED_MESSAGE = _("This confirmation key has expired.")
    INVALID_KEY_MESSAGE = _("The confirmation key you provided is invalid.")
    OVERBOOKED = _("The talk is overbooked.")
    WRONG_USER = _("You can confirm your own reservations only.")
    template_name = "talk/sessionreservation_confirm_failed.html"

    reservation = None

    def get_success_url(self, reservation=None):
        return reverse(
            "talk_reservation_confirmed",
            kwargs={"event": self.event.slug, "slug": reservation.talk.slug},
        )

    def confirm_reservation(self, *args, **kwargs):
        self.reservation = self.validate_key(kwargs.get("confirmation_key"))
        if self.reservation.attendee.user != self.request.user:
            raise ConfirmationError(self.WRONG_USER, code="wrong_user")
        if (
            self.reservation.talk.spots
            <= SessionReservation.objects.filter(
                is_confirmed=True, talk_id=self.reservation.talk_id
            ).count()
        ):
            self.reservation.is_waiting = True
            self.reservation.save()
            raise ConfirmationError(self.OVERBOOKED, code="overbooked")
        self.reservation.is_confirmed = True
        self.reservation.save()

    def validate_key(self, confirmation_key):
        try:
            data = signing.loads(
                confirmation_key,
                salt=settings.CONFIRMATION_SALT,
                max_age=settings.TALK_RESERVATION_CONFIRMATION_DAYS * 86400,
            )
            username, talk_id = data.split(":")
            return get_object_or_404(
                SessionReservation,
                attendee__user__email=username,
                attendee__user__is_active=True,
                talk_id=int(talk_id),
            )
        except signing.SignatureExpired:
            raise ConfirmationError(self.EXPIRED_MESSAGE, code="expired")
        except signing.BadSignature:
            raise ConfirmationError(
                self.INVALID_KEY_MESSAGE,
                code="invalid_key",
                params={"confirmation_key": confirmation_key},
            )

    def get(self, request, *args, **kwargs):
        extra_context = {}
        try:
            self.confirm_reservation(*args, **kwargs)
        except ConfirmationError as e:
            extra_context["confirmation_error"] = {
                "message": e.message,
                "code": e.code,
                "params": e.params,
            }
        else:
            signals.session_reservation_confirmed.send(
                sender=self.__class__,
                reservation=self.reservation,
                request=self.request,
            )
            return HttpResponseRedirect(
                force_text(self.get_success_url(self.reservation))
            )
        context_data = self.get_context_data()
        context_data.update(extra_context)
        return self.render_to_response(context_data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"event": self.event, "reservation": self.reservation})
        return context


class TalkReservationConfirmed(AttendeeRequiredMixin, TemplateView):
    template_name = "talk/sessionreservation_confirmed.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {"event": self.event, "talk": get_object_or_404(Talk, slug=kwargs["slug"])}
        )
        return context


class TalkReservationWaiting(AttendeeRequiredMixin, TemplateView):
    template_name = "talk/sessionreservation_waiting.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {"event": self.event, "talk": get_object_or_404(Talk, slug=kwargs["slug"])}
        )
        return context


class LimitedTalkList(ListView):
    model = Talk
    template_name_suffix = "_limited_list"

    def get_queryset(self):
        confirmed_reservations = Prefetch(
            "sessionreservation_set",
            to_attr="confirmed_reservations",
            queryset=SessionReservation.objects.filter(is_confirmed=True),
        )
        return (
            Talk.objects.filter(
                event__slug=self.kwargs.get("event"), track__isnull=False, spots__gt=0
            )
            .prefetch_related(confirmed_reservations)
            .order_by("title")
            .select_related("published_speaker")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            attendee = Attendee.objects.filter(
                event__slug=self.kwargs.get("event"), user=self.request.user
            ).first()
            if attendee:
                context["reservations"] = {
                    r.talk_id: r for r in list(attendee.sessionreservation_set.all())
                }
        return context


class AttendeeTalkFeedback(AttendeeRequiredMixin, ModelFormMixin, BaseFormView):
    model = AttendeeFeedback
    http_method_names = ["post"]
    form_class = AttendeeTalkFeedbackForm

    talk = None
    object = None

    def _fill_talk_and_attendee(self, **kwargs):
        self.talk = get_object_or_404(Talk, event=self.event, slug=kwargs["slug"])
        self.object = AttendeeFeedback.objects.filter(
            talk=self.talk, attendee=self.attendee
        ).first()

    def post(self, request, *args, **kwargs):
        self._fill_talk_and_attendee(**kwargs)
        if not (self.talk.is_feedback_allowed or self.request.user.is_staff):
            return JsonResponse({"errors": "not allowed"}, status=400)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save()
        return JsonResponse({"success": True})

    def form_invalid(self, form):
        return JsonResponse({"errors": form.errors}, status=400)

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update({"attendee": self.attendee, "talk": self.talk})
        return form_kwargs
