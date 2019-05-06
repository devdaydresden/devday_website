from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from attendee.models import Attendee
from attendee.tests import attendee_testutils
from devday.utils.devdata import DevData
from event.models import Event
from event.tests import event_testutils
from speaker.tests import speaker_testutils
from talk.forms import AddTalkSlotFormStep1, AddTalkSlotFormStep2
from talk.models import (
    AttendeeFeedback,
    Room,
    SessionReservation,
    Talk,
    TalkSlot,
    TimeSlot,
    Track,
)

User = get_user_model()


class AdminTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.event = Event.objects.get(title="devdata.18")
        cls.devdata = DevData()
        cls.devdata.create_talk_formats()
        cls.devdata.update_events()
        # we need to create more users because of the stochastic
        # subsampling for attendees
        cls.devdata.create_users_and_attendees(
            amount=cls.devdata.SPEAKERS_PER_EVENT * 2, events=[cls.event]
        )
        cls.devdata.create_speakers(events=[cls.event])
        cls.devdata.create_talks(events=[cls.event])
        cls.devdata.create_tracks(events=[cls.event])
        cls.devdata.create_rooms(events=[cls.event])
        cls.devdata.create_time_slots(events=[cls.event])
        cls.devdata.create_talk_slots(events=[cls.event])

    def setUp(self):
        self.user_password = u"s3cr3t"
        self.user = User.objects.create_superuser(
            u"admin@example.org", self.user_password
        )
        self.client.login(email=self.user.email, password=self.user_password)

    def test_talk_admin_list(self):
        response = self.client.get(reverse("admin:talk_talk_changelist"))
        self.assertEquals(response.status_code, 200)
        self.assertTrue(
            response.context["cl"].result_count > 10, "should list some talks"
        )

    def test_talk_admin_change(self):
        talk = Talk.objects.filter(event=self.event).first()
        response = self.client.get(reverse("admin:talk_talk_change", args=(talk.id,)))
        self.assertEquals(response.status_code, 200)

    def test_talk_admin_publish(self):
        talks = Talk.objects.filter(event=self.event)
        response = self.client.post(
            reverse("admin:talk_talk_changelist"),
            {
                "action": "publish_talks",
                "_selected_action": [str(talk.pk) for talk in talks],
            },
        )
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, "talk/admin/publish_talks.html")

    def test_talk_admin_publish_apply(self):
        tracks = Track.objects.filter(event=self.event)
        speaker, _, _ = speaker_testutils.create_test_speaker()

        talk = Talk.objects.create(
            draft_speaker=speaker,
            title="Test",
            abstract="Test abstract",
            remarks="Test remarks",
            event=self.event,
        )

        response = self.client.post(
            reverse("admin:talk_talk_changelist"),
            {
                "action": "publish_talks",
                "apply": "Submit",
                "_selected_action": [str(talk.pk)],
                "selected_track-{}".format(talk.pk): "",
            },
        )
        self.assertRedirects(response, reverse("admin:talk_talk_changelist"))
        talk = Talk.objects.get(pk=talk.pk)
        self.assertIsNone(talk.track_id)
        self.assertIsNone(talk.published_speaker)

        response = self.client.post(
            reverse("admin:talk_talk_changelist"),
            {
                "action": "publish_talks",
                "apply": "Submit",
                "_selected_action": [str(talk.pk)],
                "selected_track-{}".format(talk.pk): str(tracks[0].pk),
            },
        )
        self.assertRedirects(response, reverse("admin:talk_talk_changelist"))
        talk = Talk.objects.get(pk=talk.pk)
        self.assertEquals(talk.track, tracks[0])
        self.assertIsNotNone(talk.published_speaker)

    def test_talkslot_admin_list(self):
        response = self.client.get(reverse("admin:talk_talkslot_changelist"))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(
            response.context["cl"].result_count, 14, "should list 14 talkslots"
        )
        self.assertTrue(response.is_rendered)

    def test_talkslot_admin_add(self):
        speaker, _, _ = speaker_testutils.create_test_speaker()

        talk = Talk.objects.create(
            draft_speaker=speaker,
            title="Test",
            abstract="Test abstract",
            remarks="Test remarks",
            event=self.event,
        )
        track = Track.objects.filter(event=self.event).first()
        talk.publish(track)

        response = self.client.get(reverse("admin:talk_talkslot_add"))
        self.assertEquals(response.status_code, 200)
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], AddTalkSlotFormStep1)
        self.assertTemplateUsed("talk/admin/talkslot_add_form.html")

        response = self.client.post(
            reverse("admin:talk_talkslot_add"),
            {
                "add_talk_slot_view-current_step": "0",
                "0-event": str(self.event.pk),
                "submit": "Submit",
            },
        )
        self.assertEquals(response.status_code, 200)
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], AddTalkSlotFormStep2)
        self.assertTemplateUsed("talk/admin/talkslot_add_form.html")

        time_slot = TimeSlot.objects.filter(event=self.event).first()
        room = Room.objects.filter(event=self.event).first()

        response = self.client.post(
            reverse("admin:talk_talkslot_add"),
            {
                "add_talk_slot_view-current_step": "1",
                "1-talk": str(talk.pk),
                "1-time": str(time_slot.pk),
                "1-room": str(room.pk),
                "submit": "Submit",
            },
        )
        self.assertRedirects(response, reverse("admin:talk_talkslot_changelist"))
        talk_slot = TalkSlot.objects.filter(talk=talk).get()
        self.assertEquals(talk_slot.talk_id, talk.id)
        self.assertEquals(talk_slot.room_id, room.id)
        self.assertEquals(talk_slot.time_id, time_slot.id)

    def test_session_reservation_admin(self):
        speaker, _, _ = speaker_testutils.create_test_speaker()

        talk = Talk.objects.create(
            draft_speaker=speaker,
            title="Test",
            abstract="Test abstract",
            remarks="Test remarks",
            event=self.event,
        )
        track = Track.objects.filter(event=self.event).first()
        talk.publish(track)

        user, _ = attendee_testutils.create_test_user("test@example.org")
        attendee = Attendee.objects.create(user=user, event=self.event)

        SessionReservation.objects.create(attendee=attendee, talk=talk)

        response = self.client.get(reverse("admin:talk_sessionreservation_changelist"))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(
            response.context["cl"].result_count, 1, "should list 1 session registration"
        )
        self.assertTrue(response.is_rendered)


class AttendeeFeedbackAdminTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.event = event_testutils.create_test_event(title="Test event")
        user1, _ = attendee_testutils.create_test_user("test1@example.org")
        user2, _ = attendee_testutils.create_test_user("test2@example.org")
        cls.attendees = [
            Attendee.objects.create(user=user1, event=cls.event),
            Attendee.objects.create(user=user2, event=cls.event),
        ]
        speaker, _, _ = speaker_testutils.create_test_speaker()
        cls.talk = Talk.objects.create(
            draft_speaker=speaker, event=cls.event, title="Test Talk"
        )
        track = Track.objects.create(name="Test Track")
        cls.talk.publish(track)
        cls.feedback = AttendeeFeedback.objects.create(
            talk=cls.talk, attendee=cls.attendees[0], score=4, comment="Nice try"
        )

    def setUp(self):
        user_password = u"s3cr3t"
        user = User.objects.create_superuser("admin@example.org", user_password)
        self.client.login(email=user.email, password=user_password)

    def test_list(self):
        response = self.client.get(reverse("admin:talk_attendeefeedback_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.context["cl"].result_count == 1, "should list a talk feedback"
        )

    def test_change(self):
        response = self.client.get(
            reverse("admin:talk_attendeefeedback_change", args=(self.feedback.id,))
        )
        self.assertEquals(response.status_code, 200)
