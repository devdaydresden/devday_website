from django.conf import settings
from .models import Event


def current_event_contextprocessor(request):
    return {
        'current_event': Event.objects.get(pk=settings.EVENT_ID)
    }