from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from twitterfeed.models import Tweet, TwitterSetting, TwitterProfileImage


# noinspection PyUnusedLocal
def show_on_site(modeladmin, request, queryset):
    queryset.update(show_on_site=True)


show_on_site.short_description = _('show on site')


# noinspection PyUnusedLocal
def hide_on_site(modeladmin, request, queryset):
    queryset.update(show_on_site=False)


hide_on_site.short_description = _('hide on site')


@admin.register(Tweet)
class TweetAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ('user_screen_name', 'plain_text', 'show_on_site')
    list_display_links = ('plain_text',)
    list_filter = ('show_on_site',)
    readonly_fields = (
        'twitter_id', 'user_profile_image', 'user_name', 'user_screen_name', 'text',
        'plain_text', 'entities', 'created_at')
    actions = [show_on_site, hide_on_site]


admin.site.register(TwitterSetting)
admin.site.register(TwitterProfileImage)
