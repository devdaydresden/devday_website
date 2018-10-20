from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from .forms import (AttendeeInlineForm, DevDayUserChangeForm,
                    DevDayUserCreationForm)
from .models import Attendee, DevDayUser


@admin.register(Attendee)
class AttendeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'event')
    fields = ('user', 'source', 'event', 'checkin_code', 'checked_in')
    list_filter = ('event',)
    search_fields = ('user__email',)
    ordering = ('event__title', 'user__email')


class AttendeeInline(admin.TabularInline):
    model = Attendee
    fields = (('event', 'source'),)
    ordering = ('event__title',)
    extra = 0
    form = AttendeeInlineForm


@admin.register(DevDayUser)
class DevDayUserAdmin(UserAdmin):
    list_display = ('email', 'is_staff', 'speaker')
    search_fields = ('email', 'speaker__name')
    list_filter = ('attendees__event', 'is_active', 'is_staff')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined',
                                           'contact_permission_date')}),
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
