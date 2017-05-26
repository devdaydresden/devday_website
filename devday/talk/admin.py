from django.contrib import admin

from .models import Speaker, Talk, Track, Room, TimeSlot, TalkSlot, TalkMedia


class TalkMediaInline(admin.StackedInline):
    model = TalkMedia


class TalkAdmin(admin.ModelAdmin):
    list_display = ['title', 'track', 'speaker']
    inlines = [
        TalkMediaInline,
    ]


class TalkSlotAdmin(admin.ModelAdmin):
    list_display = ['time', 'room', 'talk']


admin.site.register(Speaker)
admin.site.register(Talk, TalkAdmin)
admin.site.register(Track)
admin.site.register(Room)
admin.site.register(TimeSlot)
admin.site.register(TalkSlot, TalkSlotAdmin)
