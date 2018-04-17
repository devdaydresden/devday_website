from django.contrib import admin
from django.forms import ModelChoiceField

from attendee.models import Attendee
from .models import Speaker, Talk, Track, Room, TimeSlot, TalkSlot, TalkMedia


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

    def fullname(self, obj):
        obj = obj.user.user
        return u"{} {} <{}>".format(obj.first_name, obj.last_name, obj.email)

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
    search_fields = ('title', 'speaker', 'event', 'track')
    list_filter = ['speaker__user__event']
    inlines = [
        TalkMediaInline,
        TalkSlotInline,
    ]
    ordering = ['title']

    def event(self, obj):
        return obj.speaker.user.event

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'speaker':
            kwargs['queryset'] = Speaker.objects.select_related('user', 'user__user').order_by(
                'user__user__first_name', 'user__user__last_name')
            kwargs['form_class'] = SpeakerModelChoiceField
        return super(TalkAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


class TalkSlotAdmin(admin.ModelAdmin):
    list_display = ['time', 'room', 'talk']
    list_filter = ['time__event']

    # NOTYET autocomplete_fields = list_display

    def event(self, obj):
        return obj.time.event


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
