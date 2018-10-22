#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import timedelta
from os import makedirs
from os.path import isfile, join
from shutil import copyfile

import errno
import os
import random
import sys

import lorem

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import OutputWrapper
from django.core.management.color import no_style
from django.core.paginator import Paginator
from django.utils import timezone

from cms import api
from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.models import Page
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.models.static_placeholder import StaticPlaceholder

from attendee.models import Attendee
from event.models import Event
from talk.models import (Room, Speaker, Talk, TalkFormat, TalkSlot, TimeSlot,
                         Track, Vote)
from twitterfeed.models import Tweet, TwitterProfileImage

from devday.utils.words import Words

User = get_user_model()


class DevData:
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
    nspeakerperevent = 50

    def __init__(self, stdout=None, style=None):
        self.user = None
        self.stdout = stdout if stdout else OutputWrapper(
            open(os.devnull, 'w'))
        self.style = style if style else no_style()

    def write_action(self, msg):
        self.stdout.write(msg + '... ', ending='')
        self.stdout.flush()

    def write_ok(self):
        self.stdout.write(' OK', style_func=self.style.SUCCESS)

    def write_error(self):
        self.stdout.write(' FAILED', style_func=self.style.ERROR)

    def write_notice(self, msg):
        self.stdout.write(' OK', style_func=self.style.SUCCESS, ending='')
        self.stdout.write(', ' + msg, style_func=self.style.NOTICE)

    def create_objects(self, name, thing, min_count, create, already=None):
        self.write_action('Create {}'.format(name))
        count = thing.objects.count()
        if count >= min_count:
            self.write_notice('{} {} already exist'.format(count, name))
            if already:
                self.stdout.write(already(), ending='')
            return
        try:
            r = create()
            self.write_ok()
            if r:
                self.stdout.write(r, ending='')
        except Exception:
            self.write_error()
            raise

    def create_admin_user(self):
        self.write_action('Create admin user')
        try:
            self.user = User.objects.get(email=settings.ADMINUSER_EMAIL)
            self.write_notice('{} already present'
                              .format(settings.ADMINUSER_EMAIL))
        except ObjectDoesNotExist:
            try:
                self.user = User.objects.create_user(
                    settings.ADMINUSER_EMAIL, password='admin')
                self.user.is_superuser = True
                self.user.is_staff = True
                self.user.save()
                self.write_ok()
            except Exception:  # pragma: no cover
                self.write_error()
                raise

    def update_site(self):
        self.write_action('Update site')
        try:
            site = Site.objects.get(pk=1)
            site.domain = 'devday.de'
            site.name = 'Dev Data'
            site.save()
            self.write_ok()
        except Exception:  # pragma: no cover
            self.write_error()
            raise

    def create_pages(self):
        index = api.create_page(
            title='Deutsche Homepage', language='de',
            template='devday_index.html',
            parent=None, slug='de', in_navigation=False)
        index.set_as_homepage()
        eventinfo = index.placeholders.get(slot='eventinfo')
        api.add_plugin(
            eventinfo, 'TextPlugin', 'de', body=u'''<h4>Fünf Jahre
DevDay</h4> <p>Der Dev Day feiert seinen fünften Geburtstag - und den wollen
wir mit euch verbringen! Die <strong>Konferenz</strong> für alle
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
        cfp_open = index.placeholders.get(slot='cfp_open')
        api.add_plugin(
            cfp_open, 'TextPlugin', 'de', body=u'''<h4>Call for Papers</h4>
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
''')
        save_the_date = index.placeholders.get(slot='save_the_date')
        api.add_plugin(
            save_the_date, 'TextPlugin', 'de', body=u'''<h4>Save the Date</h4>
<p>Der Dev Day 19 findet am <strong>21. Mai 2019</strong> am gewohnten Ort, der
<strong>Börse Dresden</strong> statt.</p>'''
        )
        sign_up = index.placeholders.get(slot='sign_up')
        api.add_plugin(
            sign_up, 'TextPlugin', 'de', body=u'''<h4>Jetzt anmelden</h4>
<p>Sichert euch jetzt euren kostenfreien Platz auf dem Dev Day!</p>'''
        )
        api.publish_page(index, self.user, 'de')

        api.create_page(
            title='Sponsoring', language='de', published=True,
            template=TEMPLATE_INHERITANCE_MAGIC,
            reverse_id='sponsoring', parent=None)
        api.create_page(
            title='Impressum', language='de', published=True,
            template=TEMPLATE_INHERITANCE_MAGIC,
            reverse_id='imprint', parent=None)

    def create_static_placeholder_text(self, name, lang='de', paras=3,
                                       title=None, text=None):
        self.write_action('    "{}"'.format(name))

        try:
            try:
                sph = StaticPlaceholder.objects.get(name=name)
                ph = sph.draft
                np = CMSPlugin.objects.filter(placeholder=ph,
                                              language=lang).count()
                if np >= 1:
                    self.stdout.write('OK', style_func=self.style.SUCCESS)
                    return
            except ObjectDoesNotExist:
                ph, created = Placeholder.objects.update_or_create(slot=name)
                sph = StaticPlaceholder(name=name, code=name, draft=ph,
                                        dirty=True)
                sph.draft = ph
                sph.save()
                sph.publish(None, lang, True)
                # this shouldn't be necessary, but leaving it out will lead
                # to an empty placeholder.
                sph = StaticPlaceholder.objects.get(name=name)
                ph = sph.draft
            if not text:
                text = ''
                for i in range(paras):
                    text += "<p>{}</p>\n".format(lorem.paragraph())
            if title:
                text = "<h1>{}</h1>\n{}".format(title, text)
            p = api.add_plugin(ph, 'TextPlugin', lang, body=text)
            p.save()
            sph.publish(None, lang, True)
            self.stdout.write('Created', style_func=self.style.SUCCESS)
        except Exception:  # pragma: no cover
            self.write_error()
            raise

    def update_static_placeholders(self):
        self.stdout.write("Update static placeholders")
        self.create_static_placeholder_text(
            u'checkin-instructions',
            title='Check attendee in manually')
        # find devday -name "*.html" | xargs grep static_placeholder \
        # | sed -nEe 's#^.*static_placeholder "([^"]*)".*$#\1#p' | sort -u
        for placeholder in (
                u'create-talk-introtext',
                u'gdpr_teaser',
                u'register-attendee-introtext',
                u'register-intro',
                u'register-intro-anonymous',
                u'register-intro-introtext-authenticated',
                u'register-success',
                u'speaker_registered',
                u'sponsors',
                u'submit-session-introtext',
                u'submit-session-introtext-authenticated',
                u'talk_submission_closed',
                u'talk_submitted',
        ):
            self.create_static_placeholder_text(placeholder)

    def create_talk_formats(self):
        formats = [
            {'name': 'Vortrag', 'duration': 30},
            {'name': 'Lightning Talk', 'duration': 10},
            {'name': 'Workshop', 'duration': 180},
        ]
        for i in formats:
            format = TalkFormat(name=i['name'], duration=i['duration'])
            format.save()

    def update_events(self):
        self.write_action('Updating events')
        events = list(Event.objects.order_by('start_time'))
        stdformat = TalkFormat.objects.get(name='Vortrag', duration=60)
        try:
            for e in events[:-1]:
                e.registration_open = False
                e.submission_open = False
                e.save()
                e.talkformat.add(stdformat)
            e = events[-1]
            e.registration_open = True
            e.submission_open = True
            e.save()
            e.talkformat.add(*TalkFormat.objects.all())
            self.write_ok()
        except Exception:  # pragma: no cover
            self.write_error()
            raise

    def get_committee_members(self):
        r = "Program committee users:\n"
        for u in User.objects.filter(groups__name='talk_committee') \
                .order_by('email'):
            r += "    {}\n".format(u.email)
        return r

    def create_users_and_attendees(self, amount=sys.maxsize, events=None):
        if not events:
            events = Event.objects.all()
        first = ['Alexander', 'Barbara', 'Christian', 'Daniela', 'Erik',
                 'Fatima', 'Georg', 'Heike', 'Ingo', 'Jana', 'Klaus',
                 'Lena', 'Martin', 'Natalie', 'Olaf', 'Peggy', 'Quirin',
                 'Rosa', 'Sven', 'Tanja', 'Ulrich', 'Veronika', 'Werner',
                 'Xena', 'Yannick', 'Zahra']
        last = ['Schneider', 'Meier', 'Schulze', 'Fischer', 'Weber',
                'Becker', 'Lehmann', 'Koch', 'Richter', 'Neumann',
                'Fuchs', 'Vogel', 'Keller', 'Jung', 'Hahn',
                'Schubert', 'Winkler', 'Berger', 'Lorenz', 'Albrecht']
        length = len(first) * len(last)
        if length > amount:
            length = amount
        self.write_action('{:d} attendees'.format(length))
        for f in first:
            for l in last:
                user = User.objects.create_user(
                    '{}.{}@example.com'.format(f.lower(), l.lower()),
                    password='attendee', first_name=f, last_name=l,
                    contact_permission_date=timezone.now())
                user.save()
                for e in events:
                    if self.rng.random() < 0.8:
                        Attendee.objects.create(user=user, event=e)
                amount -= 1
                if (amount <= 0):
                    return

    def create_attendees(self, amount=sys.maxsize, events=None):
        self.create_users_and_attendees(amount=amount, events=events)
        g = Group.objects.get(name='talk_committee')
        for u in self.rng.sample(list(User.objects.all()), 7):
            u.groups.add(g)
            u.save()
        return self.get_committee_members()

    def get_speakers(self):
        e = Event.objects.current_event()
        r = "The first couple of speakers for {}:\n".format(e)
        speakers = Speaker.objects.filter(user__event=e) \
            .order_by('user__user__last_name', 'user__user__first_name')
        for s in Paginator(speakers, 10).page(1).object_list:
            r += "    {}\n".format(s.user.user.email)
        return r

    def create_speakers(self, events=None):
        if not events:
            events = Event.objects.all()
        nspeaker = len(events) * self.nspeakerperevent
        attendees = Attendee.objects.filter(event__in=events)
        attendees = self.rng.sample(list(attendees), nspeaker)
        self.write_action(
            'creating {} speakers for each of the {} events'.format(
                self.nspeakerperevent, len(events)))
        if not isfile(self.speaker_portrait_path):
            try:
                makedirs(self.speaker_portrait_dir)
            except OSError as e:  # pragma: no cover
                if e.errno != errno.EEXIST:
                    raise
            copyfile(self.speaker_placeholder_source_path,
                     self.speaker_portrait_path)
        for attendee in attendees:
            speaker = Speaker(user=attendee, videopermission=True,
                              shirt_size=3, shortbio='My short bio')
            # https://stackoverflow.com/a/5256094
            speaker.portrait = speaker.portrait.field \
                .attr_class(speaker, speaker.portrait.field,
                            self.speaker_portrait_media_path)
            speaker.save()
        return self.get_speakers()

    def create_talk(self, speaker, formats):
        talk = Talk(speaker=speaker, title=Words.sentence(self.rng).title(),
                    abstract=lorem.paragraph(),
                    remarks=lorem.paragraph())
        talk.save()
        talk.talkformat.add(*self.rng.sample(
            formats, self.rng.randint(1, len(formats))))
        return talk

    def create_talks(self):
        """
        Create talks. With a probability of 10%, a speaker will submit two
        talks, with a probability of 75% will submit one talk, and with a
        remaining probability of 15% will not submit any talk for the event the
        speaker registered for.
        """
        formats = list(TalkFormat.objects.all())
        for speaker in Speaker.objects.all():
            p = self.rng.random()
            if p < 0.85:
                self.create_talk(speaker, formats)
            if p < 0.10:
                self.create_talk(speaker, formats)

    def vote_for_talk(self):
        committee = User.objects.filter(groups__name='talk_committee')
        for talk in Talk.objects.filter(
                speaker__user__event=Event.objects.current_event()):
            for u in committee:
                p = self.rng.randint(0, 6)
                if p > 0:
                    vote = Vote(voter=u, talk=talk, score=p)
                    vote.save()
        return 'Cast {} votes'.format(Vote.objects.count())

    def create_tracks(self):
        tracks = {
            'devdata.17': [
                'The Human Side', 'Architektur', 'Let Data Rule', 'DevOps',
                'Keynote',
            ],
            'devdata.18': [
                'Methodik', 'Frontend', 'Coding', 'Keynote',
                'The Human Side', 'Exkursion',
            ],
        }
        for (e, ts) in tracks.items():
            event = Event.objects.get(title=e)
            for n in ts:
                track = Track(name=n, event=event)
                track.save()

    def create_rooms(self):
        p = 0
        for n in ['Hamburg', 'Gartensaal', 'St. Petersburg', 'Rotterdam']:
            room = Room(
                name=n, event=Event.objects.current_event(), priority=p)
            room.save()
            p += 1

    def create_time_slots(self, events=None):
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
        if not events:
            events = Event.objects.all()
        for t in time_slots:
            n = u'{:02d}:{:02d} \u2014 {:02d}:{:02d}'.format(t[0], t[1],
                                                             t[2], t[3])
            for event in events:
                s = event.start_time.replace(hour=t[0], minute=t[1])
                e = event.end_time.replace(hour=t[2], minute=t[3])
                timeslot = TimeSlot(name=n, event=event,
                                    start_time=s, end_time=e,
                                    text_body=t[4])
                timeslot.save()

    def create_talk_slots(self, events=None):
        keynote_room = Room.objects.get(name='Hamburg')
        rooms = Room.objects.all()
        details = ''
        if not events:
            events = Event.objects.exclude(
                    pk=Event.objects.current_event_id())
        for event in events:
            tracks = Track.objects.filter(event=event) \
                .exclude(name='Keynote')
            keynote_track = Track.objects.get(event=event, name='Keynote')
            keynotes = TimeSlot.objects.filter(event=event,
                                               text_body='Keynote')
            sessions = TimeSlot.objects.filter(event=event, text_body='')
            ntalks = len(keynotes) + len(sessions) * len(rooms)
            details += ('    {}: {} talks for {} keynotes, and {} sessions'
                        ' in {} rooms'
                        "\n").format(event.title, ntalks, len(keynotes),
                                     len(sessions), len(rooms))
            talks = self.rng.sample(
                list(Talk.objects.filter(speaker__user__event=event)), ntalks)
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
        return details

    def create_twitter_profiles(self):
        profile_image = TwitterProfileImage.objects.create(
            user_profile_image_url='http://localhost/twitter_profile.png')
        # https://stackoverflow.com/a/5256094
        profile_image.image_data = profile_image.image_data.field \
            .attr_class(profile_image, profile_image.image_data,
                        self.speaker_portrait_media_path)
        profile_image.save()

    def create_tweets(self, count=7):
        profile_image = TwitterProfileImage.objects.get(
            user_profile_image_url='http://localhost/twitter_profile.png')
        dt = timezone.now() - timedelta(days=-count)
        for i in range(count):
            user = self.rng.choice(list(User.objects.all()))
            handle = '{}{}'.format(user.first_name, user.last_name).lower()
            text = lorem.sentence()
            Tweet.objects.create(
                twitter_id=i,
                user_profile_image=profile_image,
                user_name='{} {}'.format(user.first_name, user.last_name),
                user_screen_name=handle,
                text=text,
                plain_text=text,
                entities='{}',
                created_at=dt,
                show_on_site=True)
            dt += timedelta(days=1, hours=self.rng.randrange(3),
                            minutes=self.rng.randrange(30))

    def create_devdata(self):
        self.create_admin_user()
        self.update_site()
        self.update_static_placeholders()
        self.create_objects('talk formats', TalkFormat, 3,
                            self.create_talk_formats)
        self.update_events()
        self.create_objects('pages', Page, 3, self.create_pages)
        self.create_objects('users', User, 3, self.create_attendees,
                            self.get_committee_members)
        self.create_objects('speakers', Speaker, 1, self.create_speakers,
                            self.get_speakers)
        self.create_objects('talks', Talk, 1, self.create_talks)
        self.create_objects('votes', Vote, 1, self.vote_for_talk)
        self.create_objects('tracks', Track, 1, self.create_tracks)
        self.create_objects('rooms', Room, 1, self.create_rooms)
        self.create_objects('time slots', TimeSlot, 1, self.create_time_slots)
        self.create_objects('talk slots', TalkSlot, 1, self.create_talk_slots)
        self.create_objects('twitter profiles', TwitterProfileImage, 1,
                            self.create_twitter_profiles)
        self.create_objects('tweets', Tweet, 1, self.create_tweets)
