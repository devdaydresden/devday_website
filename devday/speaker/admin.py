from django.contrib import admin

from .models import PublishedSpeaker, Speaker


@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    list_display = ('name', 'twitter_handle', 'position', 'organization')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('video_permission',)
    search_fields = ('name', 'twitter_handle', 'position', 'organization')


@admin.register(PublishedSpeaker)
class PublishedSpeakerAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'event', 'twitter_handle', 'position', 'organization')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('video_permission', 'event')
    search_fields = ('name', 'twitter_handle', 'position', 'organization')
