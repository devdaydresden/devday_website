from django.contrib import admin
from django.forms import ModelChoiceField
from django.utils.translation import gettext_lazy as _

from attendee.models import Attendee
from .models import (Speaker, Talk, TalkFormat, Track, Room, TimeSlot,
                     TalkSlot, TalkMedia)


class AttendeeModelChoiceField(ModelChoiceField):

    def label_from_instance(self, obj):
        return "{} ({})".format(obj, obj.event)


class SpeakerAdmin(admin.ModelAdmin):
    list_display = ['fullname', 'videopermission', 'shirt_size', 'event']
    search_fields = ['user__user__first_name', 'user__user__last_name', 'user__user__email']
    list_filter = ['user__event']
    ordering = ['-user__event__title', 'user__user__first_name', 'user__user__last_name']
    list_select_related = ('user', 'user__event', 'user__user')

    def event(self, obj):
        return obj.user.event
    event.short_description = _("Event")

    def fullname(self, obj):
        obj = obj.user.user
        return u"{} {} <{}>".format(obj.first_name, obj.last_name, obj.email)
    fullname.short_description = _("Fullname")

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'user':
            kwargs['queryset'] = Attendee.objects.select_related('user', 'event').order_by(
                '-event__title', 'user__first_name', 'user__last_name')
            kwargs['form_class'] = AttendeeModelChoiceField
            return super(SpeakerAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


class TalkMediaInline(admin.StackedInline):
    model = TalkMedia


class TalkSlotInline(admin.StackedInline):
    model = TalkSlot
    fields = (('room', 'time'),)


class SpeakerModelChoiceField(ModelChoiceField):

    def label_from_instance(self, obj):
        return "{} ({})".format(obj, obj.user.event)


class TalkAdmin(admin.ModelAdmin):
    list_display = ('title', 'speaker', 'event', 'track')
    search_fields = (
        'title', 'speaker__user__user__first_name', 'speaker__user__user__last_name', 'speaker__user__event__title',
        'track__name')
    list_filter = ['speaker__user__event', 'track']
    inlines = [
        TalkMediaInline,
        TalkSlotInline,
    ]
    ordering = ['title']
    list_select_related = ['speaker', 'speaker__user', 'speaker__user__event', 'speaker__user__user', 'track']
    filter_horizontal = ('talkformat', )

    def event(self, obj):
        return obj.speaker.user.event

    event.short_description = _('Event')

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'speaker':
            kwargs['queryset'] = Speaker.objects.select_related('user', 'user__user', 'user__event').order_by(
                'user__user__first_name', 'user__user__last_name')
            kwargs['form_class'] = SpeakerModelChoiceField
        return super(TalkAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


class TalkSlotAdmin(admin.ModelAdmin):
    list_display = ['time', 'event', 'room', 'talk']
    list_filter = ['time__event']

    # NOTYET autocomplete_fields = list_display

    def event(self, obj):
        return obj.time.event

    event.short_desription = _('Event')


class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['name', 'event', 'start_time', 'end_time']
    list_filter = ['event']
    ordering = ['-event__title', 'start_time']


class TrackAdmin(admin.ModelAdmin):
    list_display = ['name', 'event']
    list_filter = ['event']
    ordering = ['-event__title', 'name']


class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'event']
    list_filter = ['event']
    ordering = ['-event__title', 'name']


admin.site.register(Speaker, SpeakerAdmin)
admin.site.register(Talk, TalkAdmin)
admin.site.register(Track, TrackAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(TimeSlot, TimeSlotAdmin)
admin.site.register(TalkSlot, TalkSlotAdmin)
