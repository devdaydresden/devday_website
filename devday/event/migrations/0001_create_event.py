# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import migrations, models

from datetime import datetime


class Migration(migrations.Migration):

    def create_devday_17(self):
        Event = apps.get_model("event", "Event")
        event = Event.create(id=1, title='devday.17', slug='devday-17',
            description='DevDay.17 am 4.4. in Dresden', location='Dresden',
            full_day=false, start_time=datetime(2017, 4, 4, 13, 0),
            end_time=datetime(2017, 4, 4, 20, 0))
        event.save()

    replaces = [('event', '0001_initial'), ('event', '0002_auto_20170917_1155'),
        ('0001_squashed_0002_auto_20170917_1155')]

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=256, unique=True, verbose_name='Event title')),
                ('slug', models.SlugField(unique=True, verbose_name='Short name for URLs')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('location', models.TextField(blank=True, verbose_name='Location')),
                ('full_day', models.BooleanField(default=False, verbose_name='Full day event')),
                ('start_time', models.DateTimeField(verbose_name='Start time')),
                ('end_time', models.DateTimeField(verbose_name='End time')),
            ],
            options={
                'verbose_name': 'Event',
                'verbose_name_plural': 'Events',
            },
        ),
        migrations.RunPython(create_devday_17),
    ]
