from functools import update_wrapper

from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _, ngettext_lazy
from formtools.wizard.views import SessionWizardView

from event.models import Event
from talk.forms import SessionReservationForm, TalkSlotForm, \
    AddTalkSlotFormStep2, AddTalkSlotFormStep1
from .models import (Room, Talk, TalkFormat, TalkMedia, TalkSlot, TimeSlot,
                     Track, SessionReservation)


class TalkMediaInline(admin.StackedInline):
    model = TalkMedia


class TalkSlotInline(admin.StackedInline):
    model = TalkSlot
    fields = (('room', 'time'),)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'event']
    list_filter = ['event']
    ordering = ['-event__title', 'name']


@admin.register(Talk)
class TalkAdmin(admin.ModelAdmin):
    list_display = ('title', 'draft_speaker', 'event', 'track')
    search_fields = (
        'title', 'draft_speaker__name', 'event__title',
        'track__name')
    list_filter = ['event', 'track']
    inlines = [
        TalkMediaInline,
        TalkSlotInline,
    ]
    ordering = ['title']
    list_select_related = [
        'draft_speaker', 'event', 'track', 'track__event']
    filter_horizontal = ('talkformat',)
    prepopulated_fields = {'slug': ("title",)}
    actions = ['publish_talks']

    def publish_talks(self, request, queryset):
        if 'apply' in request.POST:
            published = 0
            for talk in queryset.all():
                track_field_name = 'selected_track-{}'.format(talk.id)
                if request.POST[track_field_name]:
                    track = Track.objects.get(
                        id=int(request.POST[track_field_name]))
                    talk.publish(track)
                    published += 1
            self.message_user(
                request,
                ngettext_lazy(
                    'One Session has been published.',
                    '%(count)d sessions have been published.',
                    published
                ) % {'count': published})
            return HttpResponseRedirect(request.get_full_path())

        return render(request, 'talk/admin/publish_talks.html', context={
            'talks': queryset,
            'tracks': Track.objects.order_by('name')
        })

    publish_talks.short_description = _('Publish selected sessions')


class AddTalkSlotView(SessionWizardView):
    template_name = "talk/admin/talkslot_add_form.html"
    form_list = [AddTalkSlotFormStep1, AddTalkSlotFormStep2]

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form, **kwargs)
        context['opts'] = TalkSlot._meta
        return context

    def get_form_initial(self, step):
        data = super().get_form_initial(step)
        if step == '0':
            data['event'] = Event.objects.current_event()
        return data

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)

        if step == '1':
            kwargs['event'] = self.get_cleaned_data_for_step('0')['event']
        return kwargs

    def done(self, form_list, **kwargs):
        data = self.get_all_cleaned_data()
        TalkSlot.objects.create(
            talk=data['talk'], room=data['room'], time=data['time'])

        kwargs['admin'].message_user(
            self.request, _("Talk slot created successfully"))

        return HttpResponseRedirect(reverse('admin:talk_talkslot_changelist'))


create_talk_slot = AddTalkSlotView.as_view()


@admin.register(TalkSlot)
class TalkSlotAdmin(admin.ModelAdmin):
    list_display = ['time', 'event', 'room', 'talk']
    list_filter = ['time__event']
    list_select_related = (
        'time', 'talk', 'room', 'time__event', 'talk__published_speaker',
        'talk__published_speaker__event')
    form = TalkSlotForm

    # NOTYET autocomplete_fields = list_display, needs Django 2.x

    def event(self, obj):
        return obj.time.event

    event.short_desription = _('Event')

    def get_urls(self):
        def wrap(view):
            def wrapper(*args, **kwargs):
                kwargs['admin'] = self
                return self.admin_site.admin_view(view)(*args, **kwargs)

            return update_wrapper(wrapper, view)

        return [
                   url(r'^add/$', wrap(create_talk_slot), name='talkslot_add')
               ] + super().get_urls()


@admin.register(TalkFormat)
class TalkFormatAdmin(admin.ModelAdmin):
    pass


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['name', 'event', 'start_time', 'end_time']
    list_filter = ['event']
    ordering = ['-event__title', 'start_time']


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ['name', 'event']
    list_filter = ['event']
    ordering = ['-event__title', 'name']


@admin.register(SessionReservation)
class SessionReservationAdmin(admin.ModelAdmin):
    list_display = ('email', 'talk_title', 'is_confirmed')
    list_select_related = (
        'attendee', 'talk', 'attendee__user')
    list_filter = ('attendee__event', 'is_confirmed')
    ordering = ('talk__title', 'attendee__user__email')
    form = SessionReservationForm

    def email(self, obj):
        return obj.attendee.user.email

    def talk_title(self, obj):
        return obj.talk.title
