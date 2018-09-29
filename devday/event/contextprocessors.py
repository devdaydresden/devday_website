from .models import Event


def current_event_contextprocessor(request):
    current_event = Event.objects.current_event()
    if current_event is not None:
        return {
            'current_event': current_event,
            'talk_submission_open': current_event.submission_open,
            'attendee_registration_open': current_event.registration_open,
        }
