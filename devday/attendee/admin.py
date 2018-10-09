from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from .forms import DevDayUserCreationForm, DevDayUserChangeForm
from .models import DevDayUser


class AttendeeAdmin(ModelAdmin):
    list_display = ['__str__']


@admin.register(DevDayUser)
class DevDayUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'twitter_handle')
    search_fields = ('first_name', 'last_name', 'email', 'twitter_handle', 'organization')
    list_filter = ('attendees__event', 'is_active', 'is_staff')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'contact_permission_date')}),
        (_('Miscellaneous'), {'fields': ('twitter_handle', 'phone', 'position', 'organization')})
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
