from __future__ import unicode_literals

from django.apps import apps, AppConfig
from django.db.models.signals import post_migrate
from django.conf import settings


class SessionsConfig(AppConfig):
    name = 'talk'

    def ready(self):
        post_migrate.connect(create_talk_committee, sender=self)
        post_migrate.connect(set_default_event, sender=self)


def create_talk_committee(**kwargs):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    group, created = Group.objects.get_or_create(name='talk_committee')

    can_vote = Permission.objects.get(content_type__app_label='talk', codename='add_vote')
    can_comment = Permission.objects.get(content_type__app_label='talk', codename='add_talkcomment')
    group.permissions.set([can_comment, can_vote])

    group.save()


def set_default_event(verbosity=2, **kwargs):
    Event = apps.get_model('event', 'Event')
    default_event = Event.objects.get(pk=getattr(settings, 'EVENT_ID'))

    Room = apps.get_model('talk', 'Room')
    rooms = Room.objects.filter(event=None)
    if verbosity >= 2:
        print("Found %d rooms" % rooms.count())
    rooms.update(event=default_event)

    Talk = apps.get_model('talk', 'Talk')
    talks = Talk.objects.filter(event=None)
    if verbosity >= 2:
        print("Found %d talks" % talks.count())
    talks.update(event=default_event)

    Speaker = apps.get_model('talk', 'Speaker')
    speakers = Speaker.objects.filter(event=None)
    if verbosity >= 2:
        print("Found %d speakers" % speakers.count())
    speakers.update(event=default_event)

    Track = apps.get_model('talk', 'Track')
    tracks = Track.objects.filter(event=None)
    if verbosity >= 2:
        print("Found %d tracks" % tracks.count())
    tracks.update(event=default_event)

    Timeslot = apps.get_model('talk', 'Timeslot')
    timeslots = Timeslot.objects.filter(event=None)
    if verbosity >= 2:
        print("Found %d time slots" % timeslots.count())
    timeslots.update(event=default_event)
