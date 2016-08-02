from django.contrib import admin

from .models import Speaker, Talk

admin.site.register(Speaker)
admin.site.register(Talk)
