import csv
from io import StringIO

from django.conf import settings
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.mixins import (
    AccessMixin,
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.core import signing
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Avg, Count, Prefetch, Q
from django.db.transaction import atomic
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DeleteView, DetailView, TemplateView, UpdateView, View
from django.views.generic.edit import FormView, ModelFormMixin
from django.views.generic.list import BaseListView, ListView
from django_registration import signals
from django_registration.backends.activation.views import (
    ActivationView,
    RegistrationView,
)
from django_registration.exceptions import ActivationError

from attendee.forms import (
    AttendeeEventFeedbackForm,
    AttendeeProfileForm,
    AttendeeRegistrationForm,
    BadgeDataForm,
    CheckInAttendeeForm,
    DevDayUserRegistrationForm,
    EventRegistrationForm,
    RegistrationAuthenticationForm,
)
from attendee.signals import attendence_cancelled
from event.models import Event
from talk.models import Attendee, SessionReservation, Talk

from .models import AttendeeEventFeedback, BadgeData, DevDayUser

User = get_user_model()

REGISTRATION_SALT = getattr(settings, "REGISTRATION_SALT", "registration")


class AttendeeQRCodeMixIn(object):
    # noinspection PyUnresolvedReferences
    def attendee_qrcode_context(self, context):
        attendee = self.request.user.attendees.order_by("-event__start_time").first()
        if attendee:
            context["checked_in"] = attendee.checked_in is not None
            if context["checked_in"]:
                context.update(
                    {
                        "message": _("You are already checked in."),
                        "checkin_code": attendee.checkin_code,
                        "message_code": "already",
                    }
                )
            else:
                context.update(
                    {
                        "url": self.request.build_absolute_uri(
                            attendee.get_checkin_url(attendee.event)
                        ),
                        "checkin_code": attendee.checkin_code,
                        "message_code": "OK",
                    }
                )
        else:
            context.update(
                {
                    "checked_in": False,
                    "message": _("You are not registered for the current event."),
                    "message_code": "notregistered",
                }
            )


class AttendeeRequiredMixin(AccessMixin):
    """
    CBV mixin which verifies that the current user is an attendee for the specific event
    """

    event_slug_url_kwarg = "event"

    event = None
    attendee = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.event = get_object_or_404(
            Event, slug=kwargs[self.event_slug_url_kwarg], published=True
        )
        self.attendee = Attendee.objects.filter(
            event=self.event, user=request.user
        ).first()
        if self.attendee is None:
            if self.event.registration_open:
                return redirect("attendee_registration", event=self.event.slug)
            else:
                return redirect("django_registration_disallowed")
        # noinspection PyUnresolvedReferences
        return super().dispatch(request, *args, **kwargs)


class DevDayUserProfileView(LoginRequiredMixin, AttendeeQRCodeMixIn, UpdateView):
    model = User
    template_name = "attendee/profile.html"
    form_class = AttendeeProfileForm
    success_url = reverse_lazy("user_profile")

    def get_object(self, queryset=None):
        return self.request.user

    def get_initial(self):
        initial = super().get_initial()
        initial["accept_general_contact"] = (
            self.request.user.contact_permission_date is not None
        )
        return initial

    def get_context_data(self, **kwargs):
        context = super(DevDayUserProfileView, self).get_context_data(**kwargs)
        attendees = (
            Attendee.objects.filter(event__published=True, user_id=self.request.user.id)
            .select_related("user", "event")
            .prefetch_related(
                Prefetch(
                    "sessionreservation_set",
                    queryset=SessionReservation.objects.order_by("talk__title"),
                    to_attr="reservations",
                ),
                "reservations__talk",
                "reservations__talk__event",
            )
            .order_by("event__start_time")
        )
        context["attendees"] = attendees
        context["current_event"] = Event.objects.current_event()
        self.attendee_qrcode_context(context)
        return context


class AttendeeRegistrationView(RegistrationView):
    form_classes = {
        "anonymous": AttendeeRegistrationForm,
        "user": EventRegistrationForm,
    }
    auth_level = None
    event = None
    attendee_email_body_template = "attendee/attendee_activation_email_body.txt"
    attendee_email_subject_template = "attendee/attendee_activation_email_subject.txt"
    email_body_template = "attendee/attendee_activation_email_body_new_user.txt"
    email_subject_template = "attendee/attendee_activation_email_subject_new_user.txt"
    template_name = "attendee/attendee_registration.html"

    def dispatch(self, *args, **kwargs):
        user = self.request.user
        self.event = get_object_or_404(Event, slug=self.kwargs.get("event"))
        if not self.event.registration_open:
            return redirect("django_registration_disallowed")

        if user.is_anonymous:
            self.auth_level = "anonymous"
        elif user.get_attendee(event=self.event):
            return redirect(
                reverse_lazy("edit_badge_data", kwargs={"event": self.event.slug})
            )
        else:
            self.auth_level = "user"
        return super(AttendeeRegistrationView, self).dispatch(*args, **kwargs)

    def get_success_url(self, user=None):
        if self.auth_level == "anonymous":
            return reverse_lazy("django_registration_complete")
        return reverse_lazy(
            "attendee_registration_pending", kwargs={"event": self.event.slug}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {"auth_level": self.auth_level, "event": self.event,}
        )
        return context

    def get_form_class(self, request=None):
        return self.form_classes.get(self.auth_level, None)

    def get_form_kwargs(self):
        kwargs = super(AttendeeRegistrationView, self).get_form_kwargs()
        kwargs["event"] = self.event
        if self.request.user.is_authenticated:
            kwargs["instance"] = self.request.user
        return kwargs

    def get_email_context(self, activation_key):
        context = super(AttendeeRegistrationView, self).get_email_context(
            activation_key
        )
        context.update({"event": self.event})
        return context

    def get_attendee_activation_key(self, user_id):
        return signing.dumps(obj=user_id, salt=REGISTRATION_SALT)

    def send_attendee_confirmation_email(self, user):
        activation_key = self.get_attendee_activation_key(user.id)
        context = self.get_email_context(activation_key)
        context["user"] = user
        context["event"] = self.event
        subject = render_to_string(
            template_name=self.attendee_email_subject_template,
            context=context,
            request=self.request,
        )
        # Force subject to a single line to avoid header-injection
        # issues.
        subject = "".join(subject.splitlines())
        message = render_to_string(
            template_name=self.attendee_email_body_template,
            context=context,
            request=self.request,
        )
        user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)

    @atomic
    def register(self, form):
        if self.auth_level == "anonymous":
            user = form.save(commit=True)
            signals.user_registered.send(
                sender=self.__class__, user=user, request=self.request
            )
            self.send_activation_email(user)
            return user
        else:
            user = form.save(commit=True)
            self.send_attendee_confirmation_email(user)
            return user


class AttendeeRegistrationPendingView(TemplateView):
    """
    A view that displays a template when an attendee has registered. It should
    display an advice that the user has to confirm the attendance by clicking
    the activation link in the mail that is send by
    AttendeeRegistrationView.send_attendee_confirmation_email.
    """

    template_name = "attendee/attendee_registration_pending.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["event"] = get_object_or_404(Event, slug=self.kwargs["event"])
        return context


class DevDayUserRegistrationView(RegistrationView):
    """
    A regular registration view that can be used to register an account without
    registering for a specific event.
    """

    form_class = DevDayUserRegistrationForm
    email_body_template = "attendee/devdayuser_activation_email_body.txt"
    email_subject_template = "attendee/devdayuser_activation_email_subject.txt"

    def dispatch(self, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            return redirect(self.get_success_url())
        return super().dispatch(*args, **kwargs)

    def get_success_url(self, user=None):
        if self.request.user.is_authenticated:
            return self.request.GET.get("next", "/")
        return super().get_success_url(user)

    def get_initial(self):
        initial = super().get_initial()
        initial["next"] = self.request.GET.get("next", "")
        return initial

    def get_email_context(self, activation_key):
        context = super().get_email_context(activation_key)
        context.update({"next": self.request.POST.get("next", "")})
        return context


class DevDayUserActivationView(ActivationView):
    def get_success_url(self, user=None):
        logout(self.request)
        return "{}?next={}".format(
            reverse_lazy("auth_login"),
            self.request.GET.get("next", reverse_lazy("user_profile")),
        )


class AttendeeActivationView(ActivationView):
    event = None

    def get(self, *args, **kwargs):
        self.event = get_object_or_404(Event, slug=self.kwargs.get("event"))
        if not self.event.registration_open:
            return redirect("django_registration_disallowed")
        return super().get(*args, **kwargs)

    def activate(self, *args, **kwargs):
        user = super().activate(*args, **kwargs)
        attendee = Attendee.objects.create(event=self.event, user=user)
        BadgeData.objects.create(attendee=attendee, title=attendee.derive_title())
        return user

    def get_success_url(self, user=None):
        logout(self.request)
        return "{}?next={}".format(
            reverse_lazy("auth_login"),
            reverse_lazy(
                "attendee_register_success", kwargs={"event": self.event.slug}
            ),
        )


class AttendeeConfirmationView(LoginRequiredMixin, ActivationView):
    event = None
    template_name = "attendee/attendee_confirmation_failed.html"

    def get(self, *args, **kwargs):
        self.event = get_object_or_404(Event, slug=self.kwargs.get("event"))
        if not self.event.registration_open:
            return redirect("django_registration_disallowed")

        extra_context = {}
        try:
            self.activate(*args, **kwargs)
        except ActivationError as e:
            extra_context["activation_error"] = {
                "message": e.message,
                "code": e.code,
                "params": e.params,
            }
        else:
            return HttpResponseRedirect(force_text(self.get_success_url()))
        context_data = self.get_context_data()
        context_data.update(extra_context)
        return self.render_to_response(context_data)

    def activate(self, *args, **kwargs):
        activation_key = kwargs.get("activation_key")
        user_id = self.validate_key(activation_key)
        user = get_object_or_404(User, id=user_id)
        if self.request.user != user:
            raise ActivationError(
                message=_("Account does not match the activation code"),
                code="user_mismatch",
                params={"activation_key": activation_key, "user": self.request.user},
            )
        attendee, created = Attendee.objects.get_or_create(event=self.event, user=user)
        badge_data, created = BadgeData.objects.get_or_create(attendee=attendee)
        if created:
            badge_data.title = attendee.derive_title()
            badge_data.save()
        return attendee

    def get_success_url(self, user=None):
        return reverse_lazy(
            "attendee_register_success", kwargs={"event": self.event.slug}
        )


class AttendeeCancelView(AttendeeRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # remove attendee for user, event tuple
        attendence_cancelled.send(
            self.__class__, attendee=self.attendee, request=request
        )
        self.attendee.delete()
        return HttpResponseRedirect(reverse("user_profile"))


class AttendeeToggleRaffleView(AttendeeRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.attendee.raffle = not self.attendee.raffle
        self.attendee.save()
        return JsonResponse({"raffle": self.attendee.raffle})


class AttendeeRegisterSuccessView(AttendeeRequiredMixin, UpdateView):
    template_name = "attendee/attendee_register_success.html"
    event = None
    form_class = BadgeDataForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event"] = self.event
        return context

    def get_object(self, queryset=None):
        return get_object_or_404(BadgeData, attendee_id=self.attendee.id)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["attendee"] = self.attendee
        return kwargs

    def get_success_url(self):
        return reverse(
            "attendee_registration_complete", kwargs={"event": self.event.slug}
        )


class EditBadgeDataView(AttendeeRequiredMixin, UpdateView):
    template_name = "attendee/badge_data_edit.html"
    event = None
    form_class = BadgeDataForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event"] = self.event
        return context

    def get_object(self, queryset=None):
        return get_object_or_404(BadgeData, attendee=self.attendee)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["attendee"] = self.attendee
        return kwargs

    def get_success_url(self):
        return reverse("user_profile")


class AttendeeRegistrationCompleteView(AttendeeRequiredMixin, TemplateView):
    template_name = "attendee/attendee_register_complete.html"
    event = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event"] = self.event
        return context


class LoginOrRegisterAttendeeView(LoginView):
    """
    This view presents a choice of links for anonymous users.
    """

    template_name = "attendee/login_or_register.html"
    form_class = RegistrationAuthenticationForm
    event = None

    def get_form_kwargs(self):
        kwargs = super(LoginOrRegisterAttendeeView, self).get_form_kwargs()
        kwargs["event"] = self.event
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(LoginOrRegisterAttendeeView, self).get_context_data(**kwargs)
        context["event"] = self.event
        return context

    def dispatch(self, request, *args, **kwargs):
        self.event = Event.objects.current_event()
        if not request.user.is_anonymous and "edit" not in request.GET:
            return redirect(
                reverse("attendee_registration", kwargs={"event": self.event.slug})
            )
        return super(LoginOrRegisterAttendeeView, self).dispatch(
            request, *args, **kwargs
        )


class StaffUserMixin(UserPassesTestMixin):
    def test_func(self):
        # noinspection PyUnresolvedReferences
        return self.request.user.is_staff


class InactiveAttendeeView(StaffUserMixin, BaseListView):
    model = User

    def get_queryset(self):
        return super().get_queryset().filter(is_active=False).order_by("email")

    def render_to_response(self, context):
        output = StringIO()
        try:
            writer = csv.writer(output, delimiter=";")
            writer.writerow(("Email", "Date joined"))
            writer.writerows(
                [
                    (u.email, u.date_joined.strftime("%Y-%m-%d %H:%M:%S"),)
                    for u in context.get("object_list", [])
                ]
            )
            response = HttpResponse(
                output.getvalue(), content_type="txt/csv; charset=utf-8"
            )
            response["Content-Disposition"] = "attachment; filename=inactive.csv"
            return response
        finally:
            output.close()


class ContactableAttendeeView(StaffUserMixin, BaseListView):
    model = User

    def get_queryset(self):
        qs = (
            super(ContactableAttendeeView, self)
            .get_queryset()
            .filter(
                Q(contact_permission_date__isnull=False)
                | Q(attendees__event=Event.objects.current_event())
            )
            .order_by("email")
            .distinct()
        )
        return qs

    def render_to_response(self, context):
        output = StringIO()
        try:
            writer = csv.writer(output, delimiter=";")
            writer.writerow(("Email",))
            writer.writerows([(u.email,) for u in context.get("object_list", [])])
            response = HttpResponse(
                output.getvalue(), content_type="txt/csv; charset=utf-8"
            )
            response["Content-Disposition"] = "attachment; filename=contactable.csv"
            return response
        finally:
            output.close()


class AttendeeListView(StaffUserMixin, BaseListView):
    model = Attendee

    def get_queryset(self):
        return (
            super(AttendeeListView, self)
            .get_queryset()
            .filter(event_id=Event.objects.current_event_id())
            .order_by("user__email")
        )

    def render_to_response(self, context):
        output = StringIO()
        try:
            writer = csv.writer(output, delimiter=";")
            writer.writerow(("Email", "Date joined", "Contact permission date"))
            writer.writerows(
                [
                    (
                        attendee.user.email,
                        attendee.user.date_joined.strftime("%Y-%m-%d %H:%M:%S"),
                        attendee.user.contact_permission_date.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        if attendee.user.contact_permission_date
                        else "",
                    )
                    for attendee in context.get("object_list", [])
                ]
            )
            response = HttpResponse(
                output.getvalue(), content_type="txt/csv; charset=utf-8"
            )
            response["Content-Disposition"] = "attachment; filename=attendees.csv"
            return response
        finally:
            output.close()


class DevDayUserDeleteView(LoginRequiredMixin, DeleteView):
    model = DevDayUser

    def get_object(self, queryset=None):
        return self.request.user

    def _get_unpublished_talks(self):
        return Talk.objects.filter(
            published_speaker__isnull=True, draft_speaker__user=self.request.user
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"unpublished_talks": self._get_unpublished_talks()})
        return context

    def delete(self, request, *args, **kwargs):
        self._get_unpublished_talks().delete()
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("pages-root")


def get_reservation_list(attendee):
    msg = ""
    reservations = attendee.sessionreservation_set.filter(is_confirmed=True)
    if len(reservations) > 0:
        msg += "<h4>{}</h4><ul>".format(_("Attendee has confirmed place for"))
        for res in reservations:
            msg += "<li>{} <b>{}</b></li>".format(
                res.talk.talkformat.first().name, res.talk.title
            )
        msg += "</ul>"
    else:
        msg += "<p>{}</p>".format(_("Attendee has no reservations."))
    return msg


class CheckInAttendeeView(StaffUserMixin, SuccessMessageMixin, FormView):
    template_name = "attendee/checkin.html"
    form_class = CheckInAttendeeForm
    success_message = _("<b>{email}</b> has been checked in successfully to {event}!")

    def get_form_kwargs(self):
        context = super(CheckInAttendeeView, self).get_form_kwargs()
        context["event"] = Event.objects.get(slug=self.kwargs.get("event"))
        return context

    def form_valid(self, form):
        attendee = form.cleaned_data["attendee"]
        attendee.check_in()
        attendee.save()
        context = self.get_form_kwargs()
        context["form"] = form
        context["checkin_message"] = self.get_success_message(form.cleaned_data)
        context["checkin_reservations"] = get_reservation_list(attendee)
        return self.render_to_response(context)

    def form_invalid(self, form):
        context = self.get_form_kwargs()
        context["form"] = form
        return self.render_to_response(context)

    def get_success_message(self, cleaned_data):
        attendee = cleaned_data["attendee"]
        user = attendee.user
        event = attendee.event
        message = {"email": user.email, "event": event.title}
        return self.success_message.format_map(message)


class CheckInAttendeeQRView(LoginRequiredMixin, AttendeeQRCodeMixIn, TemplateView):
    template_name = "attendee/checkin_qrcode.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.attendee_qrcode_context(context)
        return context


class CheckInAttendeeUrlView(StaffUserMixin, TemplateView):
    template_name = "attendee/checkin_result.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event"] = Event.objects.get(slug=self.kwargs.get("event"))
        id = self.kwargs["id"]
        verification = self.kwargs["verification"]
        if not Attendee.objects.is_verification_valid(id, verification):
            context.update(
                {
                    "checkin_code": "invalid",
                    "checkin_result": _("Invalid verification URL"),
                    "checkin_message": _("Try again scanning the QR code."),
                }
            )
            return context
        try:
            attendee = Attendee.objects.get(id=id)
        except ObjectDoesNotExist:
            context.update(
                {
                    "checkin_code": "notfound",
                    "checkin_result": _("Attendee not found"),
                    "checkin_message": _("The attendee is (no longer) registered."),
                }
            )
            return context
        if attendee.event != context["event"]:
            context.update(
                {
                    "checkin_code": "wrongevent",
                    "checkin_result": _("Code is for the wrong event"),
                    "checkin_message": _("This checkin code is for another event."),
                }
            )
            return context
        try:
            attendee.check_in()
            attendee.save()
        except IntegrityError:
            context.update(
                {
                    "checkin_code": "already",
                    "checkin_result": _("Already checked in"),
                    "checkin_message": _(
                        "Attendee <b>{}</b> has checked in at {}."
                    ).format(
                        attendee.user, attendee.checked_in.strftime("%H:%M %d.%m.%y")
                    ),
                    "checkin_reservations": get_reservation_list(attendee),
                }
            )
            return context
        context.update(
            {
                "checkin_code": "OK",
                "checkin_result": _("Welcome!"),
                "checkin_message": _(
                    "Attendee <b>{}</b> was successfully checked in."
                ).format(attendee.user),
                "checkin_reservations": get_reservation_list(attendee),
            }
        )
        return context


class CheckInAttendeeSummaryView(StaffUserMixin, DetailView):
    model = Event
    template_name_suffix = "attendee_checkin_summary"
    slug_url_kwarg = "event"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = context["event"]
        attendees_for_event = Attendee.objects.filter(event=event)
        context["attendees_registered"] = attendees_for_event.count()
        context["attendees_checked_in"] = attendees_for_event.filter(
            checked_in__isnull=False
        ).count()
        limited_sessions = Talk.objects.filter(event=event, spots__gt=0)
        for talk in limited_sessions:
            talk_reservations = SessionReservation.objects.filter(
                is_confirmed=True, talk=talk
            )
            setattr(talk, "attendees_registered", talk_reservations.count())
            setattr(
                talk,
                "attendees_checked_in",
                talk_reservations.filter(attendee__checked_in__isnull=False).count(),
            )
        context["limited_sessions"] = limited_sessions
        return context


class AttendeeEventFeedbackView(AttendeeRequiredMixin, ModelFormMixin, FormView):
    form_class = AttendeeEventFeedbackForm
    slug_url_kwarg = "event"
    template_name = "attendee/event_feedback.html"

    object = None

    def _fill_object(self):
        self.object = AttendeeEventFeedback.objects.filter(
            event=self.event, attendee=self.attendee
        ).first()

    def get(self, request, *args, **kwargs):
        self._fill_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self._fill_object()
        return super().post(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial.update({"event": self.event, "attendee": self.attendee})
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"event": self.event, "attendee": self.attendee})
        return context

    def get_success_url(self):
        return reverse("pages-root")


class RaffleView(StaffUserMixin, ListView):
    model = Attendee
    event = None
    template_name = "attendee/attendee_raffle.html"

    def get_queryset(self):
        return super().get_queryset().filter(raffle=True, event=self.event)

    def get(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, slug=kwargs["event"])
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["event"] = self.event
        return context


class FeedbackSummaryView(StaffUserMixin, TemplateView):
    template_name = "attendee/event_summary.html"
    event = None

    def get(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, slug=kwargs["event"])
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feedback = AttendeeEventFeedback.objects.filter(event=self.event)
        aggregates = feedback.aggregate(
            Avg("overall_score"),
            Avg("organisation_score"),
            Avg("session_score"),
            Count("comment"),
        )
        context.update(
            {
                "feedback": aggregates,
                "overall_score_avg_percent": int(
                    100 * (aggregates["overall_score__avg"] or 0) / 5
                ),
                "organisation_score_avg_percent": int(
                    100 * (aggregates["organisation_score__avg"] or 0) / 5
                ),
                "session_score_avg_percent": int(
                    100 * (aggregates["session_score__avg"] or 0) / 5
                ),
            }
        )
        return context
