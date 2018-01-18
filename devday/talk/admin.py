from django.contrib import admin

from .models import Speaker, Talk, Track, Room, TimeSlot, TalkSlot, TalkMedia


class TalkMediaInline(admin.StackedInline):
    model = TalkMedia


class TalkAdmin(admin.ModelAdmin):
    list_display = ('title', 'speaker', 'event', 'track')
    search_fields = ('title', 'speaker', 'event', 'track')
    inlines = [
        TalkMediaInline,
    ]
    def event(self, obj):
        return obj.speaker.user.event


class TalkSlotAdmin(admin.ModelAdmin):
    list_display = ['time', 'room', 'talk']

class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['name', 'event' ]


admin.site.register(Speaker)
admin.site.register(Talk, TalkAdmin)
admin.site.register(Track)
admin.site.register(Room)
admin.site.register(TimeSlot, TimeSlotAdmin)
admin.site.register(TalkSlot, TalkSlotAdmin)
