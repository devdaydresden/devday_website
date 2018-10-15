from io import StringIO

from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.models import Page
from cms.models.pluginmodel import CMSPlugin
from cms.models.static_placeholder import StaticPlaceholder
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.management.base import OutputWrapper
from django.db.models import Count
from django.test import TestCase

from devday.utils.devdata import DevData
from event.models import Event
from speaker.models import Speaker
from talk.models import (Room, Talk, TalkFormat, TalkSlot, TimeSlot,
                         Track, Vote)
from twitterfeed.models import Tweet, TwitterProfileImage

User = get_user_model()


class DevDataTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.stdout = StringIO()
        cls.devdata = DevData(stdout=OutputWrapper(cls.stdout))

    def setUp(self):
        self.stdout.seek(0)
        self.stdout.truncate(0)

    def test_create_objects_failure(self):
        class FooManager:
            def count(self):
                return 0

        class Foo:
            objects = FooManager()

        def create():
            raise Exception('testing')

        try:
            self.devdata.create_objects('foo', Foo, 1, create)
        except Exception:
            pass
        self.assertTrue('FAILED' in self.stdout.getvalue(),
                        'should have FAILED, but got: {}'
                        .format(self.stdout.getvalue()))

    def subtest_create_admin_user(self):
        self.devdata.create_admin_user()
        u = User.objects.get(email=settings.ADMINUSER_EMAIL)
        self.assertEquals(u.email, settings.ADMINUSER_EMAIL)
        self.assertEquals(u.is_superuser, True)
        self.assertEquals(u.is_staff, True)

    def subtest_update_site(self):
        self.devdata.update_site()
        site = Site.objects.get(pk=1)
        self.assertEquals(site.domain, 'devday.de')
        self.assertEquals(site.name, 'Dev Data')

    def get_page(self, title):
        return Page.objects.get(
            title_set__title=title, title_set__published=True,
            publisher_is_draft=False)

    def check_plugin(self, page, slot, plugin_type):
        placeholder = page.placeholders.get(slot=slot)
        plugins = placeholder.get_plugins()
        self.assertEquals(len(plugins), 1,
                          '{} placeholder has exactly one plugin'
                          .format(slot))
        self.assertEquals(plugins[0].plugin_type, plugin_type,
                          '{} placeholder is of type {}'
                          .format(slot, plugin_type))

    def subtest_create_pages(self):
        self.devdata.create_objects('pages', Page, 3,
                                    self.devdata.create_pages)

        index = self.get_page('Deutsche Homepage')
        self.assertEquals(index.languages, 'de', 'Homepage is German')
        self.assertEquals(index.template, 'devday_index.html',
                          'Homepage uses correct template')
        self.assertTrue(index.is_home, 'Homepage is_home')
        self.check_plugin(index, 'eventinfo', 'TextPlugin')
        self.check_plugin(index, 'cfp_open', 'TextPlugin')
        self.check_plugin(index, 'save_the_date', 'TextPlugin')
        self.check_plugin(index, 'sign_up', 'TextPlugin')

        sponsoring = self.get_page('Sponsoring')
        self.assertEquals(sponsoring.languages, 'de', 'Sponsoring is German')
        self.assertEquals(sponsoring.template, TEMPLATE_INHERITANCE_MAGIC,
                          'Sponsoring uses correct template')

        impress = self.get_page('Impressum')
        self.assertEquals(impress.languages, 'de', 'Impress is German')
        self.assertEquals(impress.template, TEMPLATE_INHERITANCE_MAGIC,
                          'Impress uses correct template')

    def subtest_update_static_placeholders(self):
        self.devdata.update_static_placeholders()
        name = 'create-talk-introtext'
        lang = 'de'
        sph = StaticPlaceholder.objects.get(name=name)
        ph = sph.draft
        np = CMSPlugin.objects.filter(placeholder=ph,
                                      language=lang).count()
        self.assertEquals(np, 1, 'Exactly one static placeholder create')

    def subtest_create_talk_formats(self):
        self.devdata.create_objects('talk formats', TalkFormat, 3,
                                    self.devdata.create_talk_formats)
        formats = TalkFormat.objects.all().order_by('name', 'duration')
        self.assertEquals(len(formats), 4, 'There are four TalkFormats')
        self.assertEquals(formats[0].name, 'Lightning Talk')
        self.assertEquals(formats[0].duration, 10)
        self.assertEquals(formats[1].name, 'Vortrag')
        self.assertEquals(formats[1].duration, 45)
        self.assertEquals(formats[2].name, 'Vortrag')
        self.assertEquals(formats[2].duration, 60)
        self.assertEquals(formats[3].name, 'Workshop')
        self.assertEquals(formats[3].duration, 180)

    def subtest_update_events(self):
        self.devdata.update_events()
        events = list(Event.objects.order_by('start_time'))
        self.assertEquals(len(events), 3,
                          'there are three events')
        stdformat = TalkFormat.objects.get(name='Vortrag', duration=60)
        for e in events[:-1]:
            self.assertEquals(e.registration_open, False,
                              'registration not open')
            self.assertEquals(e.submission_open, False,
                              'submission not open')
            tf = e.talkformat.filter(id=stdformat.id)
            self.assertTrue(len(tf) == 1,
                            'standard format assigned')
        e = events[-1]
        self.assertEquals(e.registration_open, True,
                          'registration  open')
        self.assertEquals(e.submission_open, True,
                          'submission open')
        tf = e.talkformat.all()
        self.assertTrue(len(tf) == 4,
                        'all formats assigned')

    def subtest_get_committee_members(self):
        count = len(self.devdata.get_committee_members()
                    .strip().split('\n')) - 1  # one extra line
        self.assertEquals(count, 7, 'Seven users are committee members')

    def subtest_create_users_and_attendees(self):
        self.devdata.create_objects(
            'users', User, 3, self.devdata.create_attendees,
            self.devdata.get_committee_members)
        users = len(User.objects.all())
        self.assertTrue(520 <= users <= 522, 'About 520 users')
        events = Event.objects.annotate(natt=Count('attendee'))
        for e in events:
            self.assertTrue(users * 0.70 <= e.natt <= users * 0.80,
                            'about {:d} attend event {}: actual {}'
                            .format(int(users * 0.8), e.title, e.natt))
        self.subtest_get_committee_members()

    def subtest_get_speakers(self):
        count = len(self.devdata.get_speakers().strip().split(
            '\n')) - 1  # one extra line
        self.assertEquals(count, 10, 'At least 10 speakers')

    def subtest_create_speakers(self):
        self.devdata.create_objects(
            'speakers', Speaker, 1, self.devdata.create_speakers,
            self.devdata.get_speakers)
        speakers = 150
        number_of_speakers = Speaker.objects.count()
        self.assertTrue(
            speakers * 0.70 <= number_of_speakers <= speakers * 1.2,
            'about {:d} speakers: actual {}'
            .format(speakers, number_of_speakers))
        self.subtest_get_speakers()

    def subtest_create_talks(self):
        self.devdata.create_objects(
            'talks', Talk, 1, self.devdata.create_talks)
        speakers = 50
        # With a probability of 10% a speaker will submit 2 talks, and with
        # a probability of 75% will submit one talk. For each event, we will
        # have talk in the amount of about 0.95 times the number of speakers.
        talks = speakers * 0.95
        events = Event.objects.annotate(
            ntalk=Count('talk'))
        for e in events:
            self.assertTrue(talks * 0.75 <= e.ntalk <= talks * 1.25,
                            'about {:d} talks at event {}: actual {}'
                            .format(int(talks), e.title, e.ntalk))

    def subtest_create_votes(self):
        event = Event.objects.current_event()
        self.devdata.create_objects(
            'votes', Vote, 1, self.devdata.vote_for_talk)
        number_of_votes = Vote.objects.exclude(talk__event=event).count()
        self.assertEquals(number_of_votes, 0, 'No votes for older events')
        number_of_votes = Vote.objects.count()
        number_of_talks = Talk.objects.filter(event=event).count()
        potential_votes = number_of_talks * User.objects.filter(
            groups__name='talk_committee').count()
        self.assertTrue(
            potential_votes * 0.7 <= number_of_votes <= potential_votes,
            'about {} votes for {} talks: actual {}'.format(
                int(potential_votes * 0.8), number_of_talks, number_of_votes))

    def subtest_create_tracks(self):
        self.devdata.create_objects(
            'tracks', Track, 1, self.devdata.create_tracks)
        # FIXME implement data checks
        ntracks = Track.objects.filter(
            event=Event.objects.current_event()).count()
        self.assertEquals(ntracks, 0, 'No tracks for current event')
        ntracks = Track.objects.filter(
            event=Event.objects.get(title='devdata.17')).count()
        self.assertEquals(ntracks, 5, '5 tracks for devdata.17')
        ntracks = Track.objects.filter(
            event=Event.objects.get(title='devdata.18')).count()
        self.assertEquals(ntracks, 6, '6 tracks for devdata.18')

    def subtest_create_rooms(self):
        self.devdata.create_objects('rooms', Room, 1,
                                    self.devdata.create_rooms)
        nrooms = Room.objects.filter(
            event=Event.objects.get(title='devdata.17')).count()
        self.assertEquals(nrooms, 4, 'we have 4 rooms for devdata.17')
        nrooms = Room.objects.filter(
            event=Event.objects.get(title='devdata.18')).count()
        self.assertEquals(nrooms, 4, 'we have 4 rooms for devdata.18')

    def subtest_create_time_slots(self):
        self.devdata.create_objects('time slots', TimeSlot, 1,
                                    self.devdata.create_time_slots)
        events = Event.objects.exclude(
            id=Event.objects.current_event_id()).annotate(
            ntimeslot=Count('timeslot'))
        for e in events:
            self.assertEquals(e.ntimeslot, 13, 'we have 13 time slots for {}'
                              .format(Event))

    def subtest_create_talk_slots(self):
        self.devdata.create_objects('talk slots', TalkSlot, 1,
                                    self.devdata.create_talk_slots)
        events = Event.objects.exclude(
            id=Event.objects.current_event_id()).annotate(
            ntalkslot=Count('talk__talkslot'))
        for e in events:
            self.assertEquals(e.ntalkslot, 14, 'we have 14 talk slots for {}'
                              .format(e))

    def subtest_create_twitter_profiles(self):
        self.devdata.create_objects('twitter profiles', TwitterProfileImage, 1,
                                    self.devdata.create_twitter_profiles)
        ntpp = TwitterProfileImage.objects.count()
        self.assertEquals(ntpp, 1, 'we have 1 twitter profile picture')

    def subtest_create_tweets(self):
        self.devdata.create_objects('tweets', Tweet, 1,
                                    self.devdata.create_tweets)
        ntweets = Tweet.objects.count()
        self.assertEquals(ntweets, 7, 'we have 7 tweets')

    def test_create_devdata(self):
        self.subtest_create_admin_user()
        self.subtest_update_site()
        self.subtest_create_pages()
        self.subtest_update_static_placeholders()
        self.subtest_create_talk_formats()
        self.subtest_update_events()
        self.subtest_create_users_and_attendees()
        self.subtest_create_speakers()
        self.subtest_create_talks()
        self.subtest_create_votes()
        self.subtest_create_tracks()
        self.subtest_create_rooms()
        self.subtest_create_time_slots()
        self.subtest_create_talk_slots()
        self.subtest_create_twitter_profiles()
        self.subtest_create_tweets()

        self.stdout.seek(0)
        self.stdout.truncate(0)
        self.devdata.create_devdata()
        self.assertTrue('OK' in self.stdout.getvalue(),
                        'At least one OK in output')
        self.assertTrue('FAILED' not in self.stdout.getvalue(),
                        'No FAILED in output')
