from django.contrib import admin

from .models import Speaker, Talk, Track, Room, TimeSlot, TalkSlot, TalkMedia


class SpeakerAdmin(admin.ModelAdmin):
    list_display = ['fullname', 'videopermission', 'shirt_size', 'event']
    search_fields = ['user__user__first_name', 'user__user__last_name', 'user__user__email']
    list_filter = ['user__event']

    def event(self, obj):
        return obj.user.event

    def fullname(self, obj):
        obj = obj.user.user
        return u"{} {} <{}>".format(obj.first_name, obj.last_name, obj.email)


class TalkMediaInline(admin.StackedInline):
    model = TalkMedia


class TalkAdmin(admin.ModelAdmin):
    list_display = ('title', 'speaker', 'event', 'track')
    search_fields = ('title', 'speaker', 'event', 'track')
    list_filter = ['speaker__user__event']
    inlines = [
        TalkMediaInline,
    ]

    def event(self, obj):
        return obj.speaker.user.event


class TalkSlotAdmin(admin.ModelAdmin):
    list_display = ['time', 'room', 'talk']

class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['name', 'event' ]


admin.site.register(Speaker, SpeakerAdmin)
admin.site.register(Talk, TalkAdmin)
admin.site.register(Track)
admin.site.register(Room)
admin.site.register(TimeSlot, TimeSlotAdmin)
admin.site.register(TalkSlot, TalkSlotAdmin)
