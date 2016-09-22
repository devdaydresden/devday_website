from django.contrib import admin

from .models import Attendee, DevDayUser

admin.site.register(DevDayUser)
admin.site.register(Attendee)
