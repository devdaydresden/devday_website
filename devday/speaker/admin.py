from django.contrib import admin

from .models import PublishedSpeaker, Speaker


@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    pass


@admin.register(PublishedSpeaker)
class PublishedSpeakerAdmin(admin.ModelAdmin):
    pass
