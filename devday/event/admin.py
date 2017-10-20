from django.contrib import admin

from .models import Event


class EventAdmin(admin.ModelAdmin):
    model = Event

    prepopulated_fields = {'slug': ("title",)}


admin.site.register(Event, EventAdmin)
