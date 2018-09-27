from .models import Event


def current_event_contextprocessor(request):
    return {
        'current_event': Event.current_event()
    }
