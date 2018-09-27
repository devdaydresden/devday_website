# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.color import no_style
from django.db import DEFAULT_DB_ALIAS, connections, migrations, models
from django.utils import timezone
from django.utils.timezone import datetime


def create_devday_events_fwd(apps, schema_manager):
    Event = apps.get_model("event", "Event")
    event = Event(id=1, title='devdata.17', slug='devdata17',
                  description='Dev Data.17 am 4.4. in Dresden',
                  location='Dresden', full_day=False,
                  start_time=timezone.make_aware(datetime(2017, 4, 4, 13, 0)),
                  end_time=timezone.make_aware(datetime(2017, 4, 4, 20, 0)))
    event.save()
    event = Event(id=2, title='devdata.18', slug='devdata18',
                  description='Dev Data.18 am 24.4. in Dresden',
                  location='Dresden', full_day=False,
                  start_time=timezone.make_aware(datetime(2018, 4, 24, 13, 0)),
                  end_time=timezone.make_aware(datetime(2018, 4, 24, 20, 0)))
    event.save()
    event = Event(id=3, title='devdata.19', slug='devdata19',
                  description='Dev Data.19 am 21.5. in Dresden',
                  location='Dresden', full_day=False,
                  start_time=timezone.make_aware(datetime(2019, 5, 21, 13, 0)),
                  end_time=timezone.make_aware(datetime(2019, 5, 21, 20, 0)),
                  registration_open=True, submission_open=True)
    event.save()
    sequence_sql = connections[DEFAULT_DB_ALIAS].ops. \
        sequence_reset_sql(no_style(), [Event])
    if sequence_sql:
        with connections[DEFAULT_DB_ALIAS].cursor() as cursor:
            for command in sequence_sql:
                cursor.execute(command)


def create_devday_events_rev(apps, schema_manager):
    Event = apps.get_model("event", "Event")
    Event.objects.filter(pk=3).delete()
    Event.objects.filter(pk=2).delete()
    Event.objects.filter(pk=1).delete()


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=256, unique=True,
                                           verbose_name='Event title')),
                ('slug', models.SlugField(unique=True,
                                          verbose_name='Short name for URLs')),
                ('description', models.TextField(blank=True,
                                                 verbose_name='Description')),
                ('location', models.TextField(blank=True,
                                              verbose_name='Location')),
                ('full_day', models
                    .BooleanField(default=False,
                                  verbose_name='Full day event')),
                ('start_time', models
                    .DateTimeField(verbose_name='Start time')),
                ('end_time', models.DateTimeField(verbose_name='End time')),
            ],
            options={
                'verbose_name': 'Event',
                'verbose_name_plural': 'Events',
            },
        ),
        migrations.RunPython(create_devday_events_fwd, create_devday_events_rev),
    ]
