"""
Creates the default Event object.
"""
from django.apps import apps
from django.conf import settings
from django.core.management.color import no_style
from django.db import DEFAULT_DB_ALIAS, connections, router
from django.utils.text import slugify
from django.utils.timezone import now


def create_default_event(app_config, verbosity=2, interactive=True, using=DEFAULT_DB_ALIAS, **kwargs):
    try:
        Event = apps.get_model('event', 'Event')
    except LookupError:
        return

    if not router.allow_migrate_model(using, Event):
        return

    if not Event.objects.using(using).exists():
        if verbosity >= 2:
            print("Creating Event object")
        event_title = getattr(settings, 'EVENT_TITLE', 'devday')
        event_slug = getattr(settings, 'EVENT_SLUG', slugify(event_title))
        Event(
            pk=getattr(settings, 'EVENT_ID', 1), title=event_title, slug=event_slug,
            start_time=now(), end_time=now()).save(using=using)

        # We set an explicit pk instead of relying on auto-incrementation,
        # so we need to reset the database sequence. See #17415.
        sequence_sql = connections[using].ops.sequence_reset_sql(no_style(), [Event])
        if sequence_sql:
            if verbosity >= 2:
                print("Resetting sequence")
            with connections[using].cursor() as cursor:
                for command in sequence_sql:
                    cursor.execute(command)
