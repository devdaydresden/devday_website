from functools import update_wrapper

from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy
from formtools.wizard.views import SessionWizardView

from attendee.models import Attendee
from event.models import Event
from speaker.models import PublishedSpeaker, Speaker
from talk.forms import (
    AddTalkSlotFormStep1,
    AddTalkSlotFormStep2,
    SessionReservationForm,
    TalkSlotForm,
)
from talk.signals import send_reservation_confirmation_mail

from .models import (
    AttendeeFeedback,
    Room,
    SessionReservation,
    Talk,
    TalkDraftSpeaker,
    TalkFormat,
    TalkMedia,
    TalkPublishedSpeaker,
    TalkSlot,
    TimeSlot,
    Track,
)


class PrefetchAdmin(object):
    # noinspection PyUnresolvedReferences
    def get_field_queryset(self, db, db_field, request):
        qs = super().get_field_queryset(db, db_field, request)
        if db_field.name in self.queryset_prefetch_fields:
            prefetch_fields = self.queryset_prefetch_fields[db_field.name]
            if qs is None:
                qs = prefetch_fields[0].objects.select_related(*prefetch_fields[1])
            else:
                qs = qs.select_related(*prefetch_fields[1])
        return qs


class TalkMediaInline(admin.StackedInline):
    model = TalkMedia


class TalkSlotInline(PrefetchAdmin, admin.StackedInline):
    model = TalkSlot
    fields = (("room", "time"),)

    queryset_prefetch_fields = {
        "room": (Room, ("event",)),
        "time": (TimeSlot, ("event",)),
    }

    def get_queryset(self, request):
        return (
            super().get_queryset(request).select_related("room", "time", "room__event")
        )


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ["name", "event"]
    list_filter = ["event"]
    ordering = ["-event__title", "name"]


class TalkDraftSpeakerInline(PrefetchAdmin, admin.StackedInline):
    model = TalkDraftSpeaker
    extra = 1
    fields = ("draft_speaker",)

    queryset_prefetch_fields = {"draft_speaker": (Speaker, ("user",))}


class TalkPublishedSpeakerInline(PrefetchAdmin, admin.StackedInline):
    model = TalkPublishedSpeaker
    extra = 1
    fields = ("published_speaker",)

    queryset_prefetch_fields = {"published_speaker": (PublishedSpeaker, ("event",))}

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        field.queryset = field.queryset.filter(event__exact=request._obj_.event)
        return field


@admin.register(Talk)
class TalkAdmin(PrefetchAdmin, admin.ModelAdmin):
    list_display = ("title", "draft_speakers_joined", "event", "track")
    search_fields = ("title", "draft_speakers__name", "event__title", "track__name")
    list_filter = ["event", "track"]
    inlines = [
        TalkDraftSpeakerInline,
        TalkPublishedSpeakerInline,
        TalkMediaInline,
        TalkSlotInline,
    ]
    ordering = ["title"]
    list_select_related = ["event", "track", "track__event"]
    filter_horizontal = ("talkformat",)
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("event",)
    actions = ["publish_talks", "process_waiting_list"]

    queryset_prefetch_fields = {
        "draft_speakers": (Speaker, ("user",)),
        "published_speakers": (PublishedSpeaker, ("speaker", "speaker__user", "event")),
        "track": (Track, ("event",)),
    }

    def draft_speakers_joined(self, obj):
        return ", ".join([speaker.name for speaker in obj.draft_speakers.all()])

    draft_speakers_joined.name = _("Draft speakers")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("event", "track", "track__event")
            .prefetch_related("draft_speakers", "published_speakers")
        )

    def publish_talks(self, request, queryset):
        if "apply" in request.POST:
            published = 0
            for talk in queryset.all():
                track_field_name = "selected_track-{}".format(talk.id)
                if request.POST[track_field_name]:
                    track = Track.objects.get(id=int(request.POST[track_field_name]))
                    talk.publish(track)
                    published += 1
            self.message_user(
                request,
                ngettext_lazy(
                    "One Session has been published.",
                    "%(count)d sessions have been published.",
                    published,
                )
                % {"count": published},
            )
            return HttpResponseRedirect(request.get_full_path())

        return render(
            request,
            "talk/admin/publish_talks.html",
            context={"talks": queryset, "tracks": Track.objects.order_by("name")},
        )

    publish_talks.short_description = _("Publish selected sessions")

    def process_waiting_list(self, request, queryset):
        mailcount = 0
        attendees = set()
        for talk in queryset.filter(
            spots__gt=0, event_id=Event.objects.current_event_id()
        ):
            confirmed_reservations = SessionReservation.objects.filter(
                talk=talk, is_confirmed=True
            ).count()
            if talk.spots > confirmed_reservations:
                waiting_reservations = (
                    SessionReservation.objects.filter(talk=talk, is_waiting=True)
                    .select_related("attendee", "attendee__user")
                    .order_by("created")
                )
                for reservation in waiting_reservations[
                    : talk.spots - confirmed_reservations
                ]:
                    user = reservation.attendee.user
                    reservation.is_waiting = False
                    reservation.save()
                    send_reservation_confirmation_mail(request, reservation, user)
                    attendees.add(user.email)
                    mailcount += 1
        if mailcount > 0:
            self.message_user(
                request,
                ngettext_lazy(
                    "A confirmation mail has been sent to %(attendees)s.",
                    "%(count)d confirmation mails have been sent to %(attendees)s.",
                    mailcount,
                )
                % {"count": mailcount, "attendees": ", ".join(attendees)},
            )
        return HttpResponseRedirect(request.get_full_path())

    process_waiting_list.short_description = _(
        "Process waiting list for selected sessions"
    )

    def get_form(self, request, obj=None, change=False, **kwargs):
        request._obj_ = obj
        return super().get_form(request, obj, change, **kwargs)


class AddTalkSlotView(SessionWizardView):
    template_name = "talk/admin/talkslot_add_form.html"
    form_list = [AddTalkSlotFormStep1, AddTalkSlotFormStep2]

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form, **kwargs)
        context["opts"] = TalkSlot._meta
        return context

    def get_form_initial(self, step):
        data = super().get_form_initial(step)
        if step == "0":
            data["event"] = Event.objects.current_event()
        return data

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)

        if step == "1":
            kwargs["event"] = self.get_cleaned_data_for_step("0")["event"]
        return kwargs

    def done(self, form_list, **kwargs):
        data = self.get_all_cleaned_data()
        TalkSlot.objects.create(talk=data["talk"], room=data["room"], time=data["time"])

        kwargs["admin"].message_user(self.request, _("Talk slot created successfully"))

        return HttpResponseRedirect(reverse("admin:talk_talkslot_changelist"))


create_talk_slot = AddTalkSlotView.as_view()


@admin.register(TalkSlot)
class TalkSlotAdmin(admin.ModelAdmin):
    list_display = ["time", "event", "room", "talk"]
    list_filter = ["time__event"]
    list_select_related = ("time", "talk", "room", "time__event")
    form = TalkSlotForm

    # NOTYET autocomplete_fields = list_display, needs Django 2.x

    def event(self, obj):
        return obj.time.event

    event.short_desription = _("Event")

    def get_urls(self):
        def wrap(view):
            def wrapper(*args, **kwargs):
                kwargs["admin"] = self
                return self.admin_site.admin_view(view)(*args, **kwargs)

            return update_wrapper(wrapper, view)

        return [
            url(r"^add/$", wrap(create_talk_slot), name="talkslot_add")
        ] + super().get_urls()


@admin.register(TalkFormat)
class TalkFormatAdmin(admin.ModelAdmin):
    pass


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ["name", "event", "start_time", "end_time", "text_body"]
    list_filter = ["event"]
    ordering = ["-event__title", "start_time"]


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ["name", "event"]
    list_filter = ["event"]
    ordering = ["-event__title", "name"]


@admin.register(SessionReservation)
class SessionReservationAdmin(admin.ModelAdmin):
    list_display = ("email", "talk_title", "is_confirmed", "is_waiting")
    list_select_related = ("attendee", "talk", "attendee__user")
    list_filter = ("attendee__event", "is_confirmed", "is_waiting")
    ordering = ("talk__title", "attendee__user__email")
    form = SessionReservationForm

    def email(self, obj):
        return obj.attendee.user.email

    def talk_title(self, obj):
        return obj.talk.title


@admin.register(AttendeeFeedback)
class AttendeeFeedbackAdmin(admin.ModelAdmin):
    list_display = ("attendee_name", "talk_speakers", "talk_title", "score")
    list_select_related = ("attendee__user", "talk", "talk__event")
    readonly_fields = ("attendee", "talk")

    ordering = ("talk__title", "attendee__user__email")
    list_filter = ("talk__event",)

    def attendee_name(self, obj):
        return obj.attendee.user.email

    def talk_speakers(self, obj):
        return ", ".join(
            [
                str(s.published_speaker)
                for s in TalkPublishedSpeaker.objects.filter(talk=obj.talk)
            ]
        )

    def talk_title(self, obj):
        return obj.talk.title

    queryset_prefetch_fields = {
        "attendee": (Attendee, ("user", "event")),
        "talk": (Talk, ("title", "event")),
        "talk__published_speakers": (PublishedSpeaker, ("name", "event")),
    }

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("talk", "attendee", "attendee__user", "attendee__event")
        )
