from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from .forms import AttendeeInlineForm, DevDayUserChangeForm, DevDayUserCreationForm
from .models import Attendee, AttendeeEventFeedback, DevDayUser, BadgeData


@admin.register(Attendee)
class AttendeeAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "raffle")
    fields = ("user", "source", "event", "checkin_code", "checked_in", "raffle")
    list_filter = ("event", "raffle")
    search_fields = ("user__email",)
    ordering = ("event__title", "user__email")


class AttendeeInline(admin.TabularInline):
    model = Attendee
    fields = (("event", "source"),)
    list_select_related = ("event",)
    ordering = ("event__title",)
    extra = 0
    form = AttendeeInlineForm


@admin.register(DevDayUser)
class DevDayUserAdmin(UserAdmin):
    list_display = ("email", "is_staff", "speaker")
    search_fields = ("email", "speaker__name")
    list_filter = ("attendees__event", "is_active", "is_staff")
    list_select_related = ("speaker",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            _("Important dates"),
            {"fields": ("last_login", "date_joined", "contact_permission_date")},
        ),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )
    ordering = ("email",)
    add_form = DevDayUserCreationForm
    form = DevDayUserChangeForm
    inlines = (AttendeeInline,)


@admin.register(AttendeeEventFeedback)
class AttendeeEventFeedbackAdmin(admin.ModelAdmin):
    list_display = ("attendee_name", "event_title")
    ordering = ("event__title", "attendee__user__email")
    list_filter = ("event",)
    readonly_fields = ("attendee", "event")
    list_select_related = ("event", "attendee", "attendee__user")

    def attendee_name(self, obj):
        return obj.attendee.user.email

    def event_title(self, obj):
        return obj.event.title

    queryset_prefetch_fields = {"attendee": (Attendee, ("user", "event"))}

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("event", "attendee", "attendee__user", "attendee__event")
        )


@admin.register(BadgeData)
class BadgeDataAdmin(admin.ModelAdmin):
    list_display = ("attendee_name", "event_title", "contact")
    ordering = ("attendee__event__title", "attendee__user__email")
    list_filter = ("attendee__event",)
    readonly_fields = ("attendee",)
    list_select_related = ("attendee", "attendee__event", "attendee__user")

    def attendee_name(self, obj):
        return "{} <{}>".format(obj.title, obj.attendee.user.email)

    def event_title(self, obj):
        return obj.attendee.event.title

    queryset_prefetch_fields = {"attendee": (Attendee, ("user", "event"))}

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("attendee", "attendee__event", "attendee__user")
        )
