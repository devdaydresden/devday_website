from django.contrib import admin

from .models import Speaker, Talk, Track, Room, TimeSlot, TalkSlot


class TalkAdmin(admin.ModelAdmin):
    list_display = ['title', 'track', 'speaker']


class TalkSlotAdmin(admin.ModelAdmin):
    list_display = ['time', 'room', 'talk']


admin.site.register(Speaker)
admin.site.register(Talk, TalkAdmin)
admin.site.register(Track)
admin.site.register(Room)
admin.site.register(TimeSlot)
admin.site.register(TalkSlot, TalkSlotAdmin)
