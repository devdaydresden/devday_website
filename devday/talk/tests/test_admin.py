from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


from attendee.models import DevDayUser
from devday.utils.devdata import DevData
from event.models import Event
from talk.models import Speaker, Talk

User = get_user_model()


class AdminTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.event = Event.objects.get(title='devdata.18')
        cls.devdata = DevData()
        cls.devdata.create_talk_formats()
        cls.devdata.update_events()
        # we need to create more users because of the stochastic
        # subsampling for attendees
        cls.devdata.create_users_and_attendees(
            amount=cls.devdata.nspeakerperevent * 2,
            events=[cls.event])
        cls.devdata.create_speakers(events=[cls.event])
        cls.devdata.create_talks()
        cls.devdata.create_tracks()
        cls.devdata.create_rooms()
        cls.devdata.create_time_slots()
        cls.devdata.create_talk_slots(events=[cls.event])

    def setUp(self):
        self.user_password = u's3cr3t'
        self.user = DevDayUser.objects.create_superuser(
            u'admin@example.org', self.user_password)
        self.client.login(email=self.user.email, password=self.user_password)

    def test_speaker_admin_list(self):
        response = self.client.get(reverse('admin:talk_speaker_changelist'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['cl'].result_count, 50,
                          'should list 50 speakers')

    def test_speaker_admin_change(self):
        speaker = Speaker.objects.filter(user__event=self.event).first()
        response = self.client.get(reverse('admin:talk_speaker_change',
                                           args=(speaker.id,)))
        self.assertEquals(response.status_code, 200)

    def test_talk_admin_list(self):
        response = self.client.get(reverse('admin:talk_talk_changelist'))
        self.assertEquals(response.status_code, 200)
        self.assertTrue(response.context['cl'].result_count > 10,
                        'should list some talks')

    def test_talk_admin_change(self):
        talk = Talk.objects.filter(speaker__user__event=self.event).first()
        response = self.client.get(reverse('admin:talk_talk_change',
                                           args=(talk.id,)))
        self.assertEquals(response.status_code, 200)

    def test_talkslot_admin_list(self):
        response = self.client.get(reverse('admin:talk_talkslot_changelist'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['cl'].result_count, 14,
                          'should list 14 talkslots')
