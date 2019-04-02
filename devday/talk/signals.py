"""
Custom signals sent during the confirmation processes.

"""
from attendee.signals import attendence_cancelled
from django.conf import settings
from django.dispatch import Signal, receiver
from django.template.loader import render_to_string
from talk.models import SessionReservation
from talk.reservation import get_reservation_email_context

session_reservation_confirmed = Signal(providing_args=["reservation", "request"])

session_reservation_cancelled = Signal(providing_args=["reservation", "request"])

TALK_RESERVATION_EMAIL_SUBJECT_TEMPLATE = "talk/sessionreservation_confirm_subject.txt"
TALK_RESERVATION_EMAIL_BODY_TEMPLATE = "talk/sessionreservation_confirm_body.txt"


def send_reservation_confirmation_mail(
    request,
    reservation,
    user,
    subject_template=TALK_RESERVATION_EMAIL_SUBJECT_TEMPLATE,
    body_template=TALK_RESERVATION_EMAIL_BODY_TEMPLATE,
):
    confirmation_key = reservation.get_confirmation_key()
    context = get_reservation_email_context(reservation, request, confirmation_key)
    subject = render_to_string(
        template_name=subject_template, context=context, request=request
    )
    # Force subject to a single line to avoid header-injection
    # issues.
    subject = "".join(subject.splitlines())
    message = render_to_string(
        template_name=body_template, context=context, request=request
    )
    user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)


@receiver(session_reservation_cancelled, dispatch_uid="talk_check_pending_reservations")
def send_confirmation_mails_to_pending_reservations(sender, **kwargs):
    old_reservation = kwargs.get("reservation")
    request = kwargs.get("request")
    reservation = (
        SessionReservation.objects.filter(
            talk_id=old_reservation.talk_id, is_waiting=True
        )
        .select_related("talk", "talk__event", "attendee", "attendee__user")
        .order_by("created")
        .first()
    )
    if reservation:
        user = reservation.attendee.user
        reservation.is_waiting = False
        reservation.save()
        send_reservation_confirmation_mail(request, reservation, user)


@receiver(attendence_cancelled, dispatch_uid="talk_check_pending_reservations_attendee")
def send_confirmation_mails_to_remaining_attendees(sender, **kwargs):
    old_attendee = kwargs.get("attendee")
    request = kwargs.get("request")
    for old_reservation in SessionReservation.objects.filter(attendee=old_attendee):
        reservation = (
            SessionReservation.objects.filter(
                talk_id=old_reservation.talk_id, is_waiting=True
            )
            .select_related("talk", "talk__event", "attendee", "attendee__user")
            .order_by("created")
            .first()
        )
        if reservation:
            user = reservation.attendee.user
            reservation.is_waiting = False
            reservation.save()
            send_reservation_confirmation_mail(request, reservation, user)
