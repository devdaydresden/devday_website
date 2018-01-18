from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import Attendee, DevDayUser


class AttendeeAdmin(ModelAdmin):
    list_display = ['__str__']


class DevDayUserAdmin(ModelAdmin):
    list_display = ('title', 'twitter_handle')
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('attendees__event', 'is_active')

    def title(self, obj):
        return u"{} {} <{}>".format(obj.first_name, obj.last_name, obj.email)


admin.site.register(DevDayUser, DevDayUserAdmin)
admin.site.register(Attendee, AttendeeAdmin)
