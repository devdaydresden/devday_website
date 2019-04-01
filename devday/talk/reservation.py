"""
Functions for reservation handling.

"""
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site


def get_reservation_email_context(reservation, request, confirmation_key):
    scheme = "https" if request.is_secure() else "http"
    return {
        "scheme": scheme,
        "confirmation_key": confirmation_key,
        "expiration_days": settings.TALK_RESERVATION_CONFIRMATION_DAYS,
        "site": get_current_site(request),
        "talk": reservation.talk,
        "event": reservation.talk.event,
        "user": reservation.attendee.user,
    }
