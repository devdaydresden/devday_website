from django.contrib import admin

from .models import Event


class EventAdmin(admin.ModelAdmin):
    model = Event
    list_display = ('title', 'registration_count')
    prepopulated_fields = {'slug': ("title",)}


admin.site.register(Event, EventAdmin)
