from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import Attendee, DevDayUser


class AttendeeAdmin(ModelAdmin):
    list_display = ['__str__']


admin.site.register(DevDayUser)
admin.site.register(Attendee, AttendeeAdmin)
