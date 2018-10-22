from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (Room, Talk, TalkFormat, TalkMedia, TalkSlot, TimeSlot,
                     Track)


class TalkMediaInline(admin.StackedInline):
    model = TalkMedia


class TalkSlotInline(admin.StackedInline):
    model = TalkSlot
    fields = (('room', 'time'),)


class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'event']
    list_filter = ['event']
    ordering = ['-event__title', 'name']


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
    list_select_related = ['draft_speaker', 'published_speaker', 'event',
                           'draft_speaker__user', 'track']
    filter_horizontal = ('talkformat', )
    prepopulated_fields = {'slug': ("title",)}


class TalkSlotAdmin(admin.ModelAdmin):
    list_display = ['time', 'event', 'room', 'talk']
    list_filter = ['time__event']

    # NOTYET autocomplete_fields = list_display

    def event(self, obj):
        return obj.time.event

    event.short_desription = _('Event')


class TalkFormatAdmin(admin.ModelAdmin):
    pass


class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['name', 'event', 'start_time', 'end_time']
    list_filter = ['event']
    ordering = ['-event__title', 'start_time']


class TrackAdmin(admin.ModelAdmin):
    list_display = ['name', 'event']
    list_filter = ['event']
    ordering = ['-event__title', 'name']


admin.site.register(Room, RoomAdmin)
admin.site.register(Talk, TalkAdmin)
admin.site.register(TalkFormat, TalkFormatAdmin)
admin.site.register(TalkSlot, TalkSlotAdmin)
admin.site.register(TimeSlot, TimeSlotAdmin)
admin.site.register(Track, TrackAdmin)
