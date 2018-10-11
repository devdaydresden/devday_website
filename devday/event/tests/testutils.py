from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from event.models import Event


def create_test_event():
    return Event.objects.create(
        title='Test Event', start_time=timezone.now(),
        end_time=timezone.now() + timedelta(days=1),
        published=True, registration_open=True, submission_open=True)


def create_test_user():
    return get_user_model().objects.create_user(email=u'speaker@example.org',
                                                password=u's3cr3t')


def update_current_event(*args, **kwargs):
    e = Event.objects.current_event()
    for attr, value in kwargs.items():
        setattr(e, attr, value)
    e.save()

def unpublish_all_events():
    for event in Event.objects.all():
        event.published = False
        event.save()
