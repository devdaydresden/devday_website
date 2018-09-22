#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import makedirs
from os.path import isfile, join
from shutil import copyfile

import errno
import random

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand

from cms import api
from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.models import Page

from attendee.models import Attendee
from event.models import Event
from talk.models import Room, Speaker, Talk, TalkSlot, TimeSlot, Track, Vote

from devday.management.commands.words import Words

User = get_user_model()


class Command(BaseCommand):
    help = 'Fill database with data suitable for development'
    rng = random.Random()
    rng.seed(1)  # we want reproducable pseudo-random numbers here
    speaker_placeholder_file = 'icons8-contacts-26.png'
    speaker_placeholder_source_path = join(settings.STATICFILES_DIRS[0],
                                           'img', speaker_placeholder_file)
    speaker_portrait_media_dir = 'speakers'
    speaker_portrait_media_path = join(speaker_portrait_media_dir,
                                       speaker_placeholder_file)
    speaker_portrait_dir = join(settings.MEDIA_ROOT,
                                speaker_portrait_media_dir)
    speaker_portrait_path = join(settings.MEDIA_ROOT,
                                 speaker_portrait_media_path)

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super(Command, self).__init__(stdout, stderr, no_color)
        self.user = None

    def create_admin_user(self):
        try:
            self.user = User.objects.get(email=settings.ADMINUSER_EMAIL)
            self.stdout.write('Create admin user: {} already present'.format(
                settings.ADMINUSER_EMAIL))
        except ObjectDoesNotExist:
            self.stdout.write('Create admin user')
            self.user = User.objects.create_user(
                settings.ADMINUSER_EMAIL, password='admin')
            self.user.is_superuser = True
            self.user.is_staff = True
            self.user.save()

    def update_site(self):
        self.stdout.write('Update site')
        site = Site.objects.get(pk=1)
        site.domain = 'devday.de'
        site.name = 'Dev Data'
        site.save()

    def create_pages(self):
        npage = Page.objects.count()
        if npage > 0:
            self.stdout.write(
                'Create pages: {} page objects already exist, skipping'.format(
                    npage))
            return
        self.stdout.write('Creating pages')
        index = api.create_page(
            title='Deutsche Homepage', language='de',
            template='devday_index.html',
            parent=None, slug='de', in_navigation=False)
        eventinfo = index.placeholders.get(slot='eventinfo')
        api.add_plugin(
            eventinfo, 'TextPlugin', 'de', body=u'''<h4>Fünf Jahre DevDay</h4>
<p>Der Dev Day feiert seinen fünften Geburtstag - und den wollen wir mit euch
verbringen! Die <strong>Konferenz</strong> für alle
<strong>IT-Interessenten</strong> - Studierende oder Professionals, aus Dresden
oder auch dem anderen Ende von Deutschland - hält zu ihrem kleinen Jubiläum
einige Neuigkeiten und Überaschungen bereit, also seid gespannt und merkt euch
bereits jetzt den <strong>21.05.2019</strong> vor. Definitiv gleich bleibt
jedoch: auch 2019 ist der Dev Day für alle Teilnehmer kostenlos.</p>
<p>Organisiert wird der Dev Day durch uns, die Software Engineering Community
(kurz SECO) der T-Systems Multimedia Solutions GmbH. Wir sind ein ca.
15-köpfiges, bunt gemischtes Team größtenteils aus Software- und System
Architekten und –Entwicklern bestehend. Neben vielen kleinen Events vor allem
zum Wissensaustausch in der T-Systems MMS organisieren wir einmal im Jahr auch
den Dev Day. Unser größtes Ziel dabei: Wissensaustausch und Vernetzung über die
Grenzen von Unternehmen und Dresden hinaus.</p>
''')
        audience = index.placeholders.get(slot='audience')
        api.add_plugin(
            audience, 'TextPlugin', 'de', body=u'''<h4>Call for Papers</h4>
<p>Für den Dev Day 19 brauchen wir wieder eure Unterstützung: meldet euch als
<strong>Speaker</strong> an und schlagt uns spannende, interessante
<strong>Vorträge</strong> vor!</p>
<p>Für 2019 haben wir uns ein paar Neuigkeiten überlegt, um noch mehr Themen
Raum zu bieten.</p>
<p>Für die <strong>Vorträge haben wir dieses Mal zwei Längen</strong>: 45 und
60 Minuten. Und das <strong>Session-Grid wird größer</strong>: wir machen
statt eines Abschluss-Vortrags vier weiter, reguläre Talks.</p>
<p>Zusätzlich gibt es Raum für <strong>drei Workshops</strong> am Vormittag:
jeweils bis zu 15 Teilnehmer können zusammen <strong>drei Stunden</strong>
tiefer in ein Thema einsteigen.</p>
<p>Sichert euch jetzt euren kostenfreien Platz auf dem Dev Day!</p>
''')
        api.publish_page(index, self.user, 'de')
        api.create_page(
            title='Sessions', language='de', published=True,
            template=TEMPLATE_INHERITANCE_MAGIC, in_navigation=True,
            parent=None)
        archive = api.create_page(
            title='Archiv', language='de', published=True,
            template=TEMPLATE_INHERITANCE_MAGIC, in_navigation=True,
            parent=None)
        api.create_page(
            title='Dev Data 2017', language='de', published=True,
            template=TEMPLATE_INHERITANCE_MAGIC, redirect='/devdata17/talk',
            in_navigation=True, parent=archive)
        api.create_page(
            title='Dev Data 2018', language='de', published=True,
            template=TEMPLATE_INHERITANCE_MAGIC, redirect='/devdata18/talk',
            in_navigation=True, parent=archive)
        api.create_page(
            title='Sponsoring', language='de', published=True,
            template=TEMPLATE_INHERITANCE_MAGIC,
            reverse_id='sponsoring', parent=None)

    def create_attendees(self):
        nuser = User.objects.count()
        if nuser > 3:
            self.stdout.write(
                'Create attendees: {} users already exist, skipping'.format(
                    nuser))
            return
        events = Event.objects.all()
        first = ['Alexander', 'Barbara', 'Christian', 'Daniela', 'Erik',
                 'Fatima', 'Georg', 'Heike', 'Ingo', 'Jana', 'Klaus', 'Lena',
                 'Martin', 'Natalie', 'Olaf', 'Peggy', 'Quirin', 'Rosa',
                 'Sven', 'Tanja', 'Ulrich', 'Veronika', 'Werner', 'Xena',
                 'Yannick', 'Zahra']
        last = ['Schneider', 'Meier', 'Schulze', 'Fischer', 'Weber',
                'Becker', 'Lehmann', 'Koch', 'Richter', 'Neumann',
                'Fuchs', 'Vogel', 'Keller', 'Jung', 'Hahn',
                'Schubert', 'Winkler', 'Berger', 'Lorenz', 'Albrecht']
        self.stdout.write(
            'Creating {:d} attendees'.format(len(first) * len(last)))
        for f in first:
            for l in last:
                user = User.objects.create_user(
                    '{}.{}@example.com'.format(f.lower(), l.lower()),
                    password='attendee', first_name=f, last_name=l)
                user.save()
                for e in events:
                    if self.rng.random() < 0.8:
                        a = Attendee(user=user, event=e)
                        a.save()
        self.stdout.write('Program committee users:')
        g = Group.objects.get(name='talk_committee')
        for u in self.rng.sample(User.objects.all(), 7):
            self.stdout.write('    {}'.format(u.email))
            u.groups.add(g)
            u.save()

    def create_speakers(self):
        nspeaker = Speaker.objects.count()
        if nspeaker > 1:
            self.stdout.write(
                'Create speakers: {} speakers already exist, skipping'.format(
                    nspeaker))
            return
        nspeakerperevent = 50
        nspeaker = Event.objects.count() * nspeakerperevent
        attendees = self.rng.sample(Attendee.objects.all(), nspeaker)
        self.stdout.write(
            'Creating {} speakers for {} events'.format(
                nspeakerperevent, Event.objects.count()))
        if not isfile(self.speaker_portrait_path):
            try:
                makedirs(self.speaker_portrait_dir)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            copyfile(self.speaker_placeholder_source_path,
                     self.speaker_portrait_path)
        for attendee in attendees:
            speaker = Speaker(user=attendee, shirt_size=3,
                              videopermission=True, shortbio='My short bio')
            # https://stackoverflow.com/a/5256094
            speaker.portrait = speaker.portrait.field \
                .attr_class(speaker, speaker.portrait.field,
                            self.speaker_portrait_media_path)
            speaker.save()

    def create_talk(self, speaker):
        talk = Talk(speaker=speaker, title=Words.sentence(self.rng).title(),
                    abstract='A very short abstract.',
                    remarks='A very short remark.')
        talk.save()
        return talk

    def create_talks(self):
        """
        Create talks. With a probability of 10%, a speaker will submit two
        talks, with a probability of 75% will submit one talk, and with a
        remaining probability of 5% will not submit any talk for the event the
        speaker registered for.
        """
        ntalk = Talk.objects.count()
        if ntalk > 1:
            self.stdout.write(
                'Create talks: {} talks already exist, skipping'.format(
                    ntalk))
            return
        self.stdout.write('Creating one talk per speaker')
        for speaker in Speaker.objects.all():
            p = self.rng.random()
            if p < 0.85:
                self.create_talk(speaker)
            if p < 0.10:
                self.create_talk(speaker)

    def vote_for_talk(self):
        nvote = Vote.objects.count()
        if nvote > 1:
            self.stdout.write(
                'Vote for talks: {} votes already exists, skipping'.format(
                    nvote))
            return
        self.stdout.write('Voting for talk submissions')
        event = Event.objects.get(id=settings.EVENT_ID)
        committee = User.objects.filter(groups__name='talk_committee')
        for talk in Talk.objects.filter(speaker__user__event=event):
            for u in committee:
                p = self.rng.randint(0, 6)
                if p > 0:
                    vote = Vote(voter=u, talk=talk, score=p)
                    vote.save()
        self.stdout.write('Cast {} votes'.format(Vote.objects.count()))

    def create_tracks(self):
        ntrack = Track.objects.count()
        if ntrack > 1:
            self.stdout.write(
                'Create tracks: {} tracks already exists, skipping'.format(
                    ntrack))
            return
        self.stdout.write('Creating tracks')
        tracks = {
            'devdata.17': [
                'The Human Side', 'Architektur', 'Let Data Rule', 'DevOps',
                'Keynote',
            ],
            'devdata.18': [
                'Methodik', 'Frontend', 'Coding', 'Keynote', 'The Human Side',
                'Exkursion',
            ],
        }
        for (e, ts) in tracks.iteritems():
            event = Event.objects.get(title=e)
            for n in ts:
                track = Track(name=n, event=event)
                track.save()

    def create_rooms(self):
        nroom = Room.objects.count()
        if nroom > 1:
            self.stdout.write(
                'Create rooms: {} rooms already exists, skipping'.format(nroom))
            return
        self.stdout.write('Creating rooms')
        event = Event.objects.get(pk=settings.EVENT_ID)
        p = 0
        for n in ['Hamburg', 'Gartensaal', 'St. Petersburg', 'Rotterdam']:
            room = Room(name=n, event=event, priority=p)
            room.save()
            p += 1

    def create_time_slots(self):
        ntimeslot = TimeSlot.objects.count()
        if ntimeslot > 1:
            self.stdout.write(
                'Create time slots: {} time slots already exists, skipping'.format(
                    ntimeslot))
            return
        self.stdout.write('Creating time slots')
        time_slots = [
            [10, 30, 12, 0, 'Exkursion'],
            [12, 0, 13, 0, 'Registrierung'],
            [13, 0, 13, 15, 'Begrüßung durch die SECO'],
            [13, 15, 14, 15, 'Keynote'],
            [14, 15, 14, 30, 'Kurze Pause'],
            [14, 30, 15, 15, ''],
            [15, 15, 15, 45, 'Kaffeepause'],
            [15, 45, 16, 30, ''],
            [16, 30, 16, 45, 'Kurze Pause'],
            [16, 45, 17, 30, ''],
            [17, 30, 17, 45, 'Kurze Pause'],
            [17, 45, 18, 45, 'Keynote'],
            [18, 45, 20, 30, 'Get Together'],
        ]
        for t in time_slots:
            n = u'{:02d}:{:02d} \u2014 {:02d}:{:02d}'.format(t[0], t[1], t[2],
                                                             t[3])
            for event in Event.objects.all():
                s = event.start_time.replace(hour=t[0], minute=t[1])
                e = event.end_time.replace(hour=t[2], minute=t[3])
                timeslot = TimeSlot(name=n, event=event,
                                    start_time=s, end_time=e,
                                    text_body=t[4])
                timeslot.save()

    def create_talk_slots(self):
        ntalkslot = TalkSlot.objects.count()
        if ntalkslot > 1:
            self.stdout.write(
                ('Create talk slots: {} talk slots already exists,'
                 ' skipping').format(ntalkslot))
            return
        self.stdout.write('Creating talk slots')
        keynote_room = Room.objects.get(name='Hamburg')
        rooms = Room.objects.all()
        for event in Event.objects.exclude(pk=settings.EVENT_ID):
            tracks = Track.objects.filter(event=event).exclude(name='Keynote')
            keynote_track = Track.objects.get(event=event, name='Keynote')
            keynotes = TimeSlot.objects.filter(event=event,
                                               text_body='Keynote')
            sessions = TimeSlot.objects.filter(event=event, text_body='')
            ntalks = len(keynotes) + len(sessions) * len(rooms)
            self.stdout.write(
                ('    {}: {} talks for {} keynotes, and {} sessions in {}'
                 ' rooms').format(
                    event.title, ntalks, len(keynotes), len(sessions),
                    len(rooms)))
            talks = self.rng.sample(
                Talk.objects.filter(speaker__user__event=event), ntalks)
            for ts in keynotes:
                talk = talks.pop()
                s = TalkSlot(time=ts, room=keynote_room, talk=talk)
                s.save()
                talk.track = keynote_track
                talk.save()
            for ts in sessions:
                for room in rooms:
                    talk = talks.pop()
                    s = TalkSlot(time=ts, room=room, talk=talk)
                    s.save()
                    talk.track = self.rng.choice(tracks)
                    talk.save()

    def handle(self, *args, **options):
        self.create_admin_user()
        self.update_site()
        self.create_pages()
        self.create_attendees()
        self.create_speakers()
        self.create_talks()
        self.vote_for_talk()
        self.create_tracks()
        self.create_rooms()
        self.create_time_slots()
        self.create_talk_slots()
