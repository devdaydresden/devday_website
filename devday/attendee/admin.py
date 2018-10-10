from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import models
from django.utils.translation import ugettext_lazy as _
from .forms import (AttendeeInlineForm, DevDayUserCreationForm,
                    DevDayUserChangeForm)
from .models import DevDayUser, Attendee


@admin.register(Attendee)
class AttendeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'event')
    fields = ('user', 'source', 'event', 'checkin_code', 'checked_in')
    list_filter = ('event',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    ordering = ('event__title', 'user__email')


class AttendeeInline(admin.TabularInline):
    model = Attendee
    fields = (('event', 'source'),)
    ordering = ('event__title',)
    extra = 0
    form = AttendeeInlineForm


@admin.register(DevDayUser)
class DevDayUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff',
                    'twitter_handle')
    search_fields = ('first_name', 'last_name', 'email', 'twitter_handle',
                     'organization')
    list_filter = ('attendees__event', 'is_active', 'is_staff')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined',
                                           'contact_permission_date')}),
        (_('Miscellaneous'), {'fields': ('twitter_handle', 'phone', 'position',
                                         'organization')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    ordering = ('email',)
    add_form = DevDayUserCreationForm
    form = DevDayUserChangeForm
    inlines = (AttendeeInline,)
