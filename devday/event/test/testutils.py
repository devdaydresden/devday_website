from datetime import timedelta

from django.utils import timezone

from event.models import Event


def create_test_event():
    return Event.objects.create(
        title='Test Event', start_time=timezone.now(), end_time=timezone.now() + timedelta(days=1))
