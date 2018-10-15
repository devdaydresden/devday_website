from datetime import timedelta

from django.utils import timezone

from event.models import Event


def create_test_event(title='Test Event', **kwargs):
    _kwargs = {
        'start_time': timezone.now(),
        'end_time': timezone.now() + timedelta(days=1),
        'published': True,
        'registration_open': True,
        'submission_open': True,
    }
    _kwargs.update(kwargs)
    return Event.objects.create_event(title, **_kwargs)


def update_event(event=Event.objects.current_event(), *args, **kwargs):
    for attr, value in kwargs.items():
        setattr(event, attr, value)
    event.save()


def unpublish_all_events():
    for event in Event.objects.all():
        event.published = False
        event.save()
