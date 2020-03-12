from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from django import forms
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now

from attendee.models import Attendee
from attendee.tests import attendee_testutils
from event.models import Event
from event.tests import event_testutils
from speaker.tests import speaker_testutils
from talk.forms import (
    AttendeeTalkFeedbackForm,
    CreateTalkForm,
    EditTalkForm,
    TalkAddReservationForm,
    TalkCommentForm,
    TalkForm,
    TalkSpeakerCommentForm,
    TalkVoteForm,
)
from talk.models import Talk, TalkFormat, Track, TalkDraftSpeaker

try:
    from unittest import mock
except ImportError:  # Python 2.7 has no mock in unittest
    import mock

User = get_user_model()


class TalkFormTest(TestCase):
    def test_fields(self):
        form = TalkForm()
        self.assertListEqual(
            list(form.fields.keys()), ["title", "abstract", "remarks", "talkformat"]
        )

    def test_model(self):
        form = TalkForm()
        talk = form.save(commit=False)
        self.assertIsInstance(talk, Talk)

    def test_widgets(self):
        form = TalkForm()
        self.assertIsInstance(form.fields["title"].widget, forms.TextInput)
        self.assertIsInstance(form.fields["abstract"].widget, forms.Textarea)
        self.assertIsInstance(form.fields["remarks"].widget, forms.Textarea)
        self.assertIsInstance(
            form.fields["talkformat"].widget, forms.CheckboxSelectMultiple
        )


class CreateTalkFormTest(TestCase):
    def test_init_creates_form_helper(self):
        speaker = mock.Mock()
        event = mock.Mock(slug="bla")
        form = CreateTalkForm(draft_speaker=speaker, initial={"event": event})
        self.assertIsInstance(form.helper, FormHelper)
        self.assertEqual(
            form.helper.form_action,
            reverse("submit_session", kwargs={"event": event.slug}),
        )
        self.assertEqual(form.helper.form_id, "create-talk-form")
        self.assertEqual(form.helper.field_template, "devday/form/field.html")
        self.assertTrue(form.helper.html5_required)

    def test_init_creates_layout(self):
        speaker = mock.Mock()
        event = mock.Mock()
        form = CreateTalkForm(draft_speaker=speaker, initial={"event": event})
        self.assertIsInstance(form.helper.layout, Layout)
        layout_fields = [name for [_, name] in form.helper.layout.get_field_names()]
        self.assertEqual(len(layout_fields), 6)
        self.assertEqual(
            set(layout_fields),
            {"event", "draft_speakers", "title", "abstract", "remarks", "talkformat"},
        )

    def test_save(self):
        talk_format = TalkFormat.objects.create(name="A Talk", duration=60)
        event = Event.objects.create(
            title="Test event", slug="test_event", start_time=now(), end_time=now()
        )
        event.talkformat.add(talk_format)
        speaker, _, password = speaker_testutils.create_test_speaker()
        form = CreateTalkForm(
            draft_speaker=speaker,
            initial={"event": event},
            data={
                "event": event.id,
                "title": "Test",
                "abstract": "Test abstract",
                "remarks": "Test remarks",
                "talkformat": [talk_format.id],
            },
        )
        talk = form.save()
        self.assertIsInstance(talk, Talk)
        self.assertEqual(talk.draft_speakers.count(), 1)
        self.assertEqual(talk.draft_speakers.first(), speaker)

    def test_save_without_commit(self):
        talk_format = TalkFormat.objects.create(name="A Talk", duration=90)
        event = event_testutils.create_test_event()
        event.talkformat.add(talk_format)
        speaker, _, _ = speaker_testutils.create_test_speaker()
        form = CreateTalkForm(
            draft_speaker=speaker,
            initial={"event": event},
            data={
                "event": event.id,
                "title": "Test",
                "abstract": "Test abstract",
                "remarks": "Test remarks",
                "talkformat": [talk_format.id],
            },
        )
        talk = form.save(commit=False)
        self.assertIsInstance(talk, Talk)
        self.assertEqual(TalkDraftSpeaker.objects.filter(talk=talk).count(), 0)


class EditTalkFormTest(TestCase):
    def test_init_creates_form_helper(self):
        form = EditTalkForm()
        self.assertIsInstance(form.helper, FormHelper)
        self.assertEqual(form.helper.field_template, "devday/form/field.html")
        self.assertTrue(form.helper.html5_required)

    def test_init_creates_layout(self):
        form = EditTalkForm()
        self.assertIsInstance(form.helper.layout, Layout)
        layout_fields = [name for [_, name] in form.helper.layout.get_field_names()]
        self.assertEqual(len(layout_fields), 4)
        self.assertEqual(layout_fields, ["title", "abstract", "remarks", "talkformat"])


class TalkCommentFormTest(TestCase):
    def test_fields(self):
        form = TalkCommentForm(instance=mock.MagicMock(pk=1))
        self.assertListEqual(["comment", "is_visible"], list(form.fields))

    def test_init_creates_form_helper(self):
        form = TalkCommentForm(instance=mock.MagicMock(pk=1))
        self.assertIsInstance(form.helper, FormHelper)
        self.assertEqual(form.fields["comment"].widget.attrs["rows"], 2)
        self.assertEqual(form.helper.form_action, "/committee/talks/1/comment/")

    def test_init_creates_layout(self):
        form = TalkCommentForm(instance=mock.MagicMock(pk=1))
        self.assertIsInstance(form.helper.layout, Layout)
        layout_fields = [name for [_, name] in form.helper.layout.get_field_names()]
        self.assertListEqual(["comment", "is_visible"], layout_fields)
        self.assertEqual(
            len(form.helper.layout.get_layout_objects(Submit, greedy=True)), 1
        )


class TalkSpeakerCommentFormTest(TestCase):
    def test_fields(self):
        form = TalkSpeakerCommentForm(instance=mock.MagicMock(pk=1))
        self.assertListEqual(["comment"], list(form.fields))

    def test_init_creates_form_helper(self):
        form = TalkSpeakerCommentForm(instance=mock.MagicMock(pk=1))
        self.assertIsInstance(form.helper, FormHelper)
        self.assertEqual(form.helper.form_action, "/session/speaker/talks/1/comment/")

    def test_init_creates_layout(self):
        form = TalkSpeakerCommentForm(instance=mock.MagicMock(pk=1))
        self.assertIsInstance(form.helper.layout, Layout)
        layout_fields = [name for [_, name] in form.helper.layout.get_field_names()]
        self.assertListEqual(["comment"], layout_fields)
        self.assertEqual(
            len(form.helper.layout.get_layout_objects(Submit, greedy=True)), 1
        )


class TalkVoteFormTest(TestCase):
    def test_fields(self):
        form = TalkVoteForm()
        self.assertListEqual(["score"], list(form.fields))


class TalkAddReservationFormTest(TestCase):
    def test_save_checks_availability_no_confirmations(self):
        event = Event.objects.current_event()
        speaker, _, _ = speaker_testutils.create_test_speaker()
        talk = Talk.objects.create(
            draft_speaker=speaker, event=event, title="Test talk", spots=1
        )
        track = Track.objects.create(name="Test track")
        talk.publish(track)

        user1, _ = attendee_testutils.create_test_user()
        attendee1 = Attendee.objects.create(user=user1, event=event)
        user2, _ = attendee_testutils.create_test_user("test2@example.org")
        attendee2 = Attendee.objects.create(user=user2, event=event)

        form = TalkAddReservationForm(attendee=attendee1, talk=talk, data={})
        form.full_clean()
        reservation1 = form.save()
        self.assertFalse(reservation1.is_waiting)
        self.assertFalse(reservation1.is_confirmed)

        form = TalkAddReservationForm(attendee=attendee2, talk=talk, data={})
        form.full_clean()
        reservation2 = form.save()
        self.assertFalse(reservation2.is_waiting)
        self.assertFalse(reservation2.is_confirmed)

    def test_save_checks_availability_with_confirmation(self):
        event = Event.objects.current_event()
        speaker, _, _ = speaker_testutils.create_test_speaker()
        talk = Talk.objects.create(
            draft_speaker=speaker, event=event, title="Test talk", spots=1
        )
        track = Track.objects.create(name="Test track")
        talk.publish(track)

        user1, _ = attendee_testutils.create_test_user()
        attendee1 = Attendee.objects.create(user=user1, event=event)
        user2, _ = attendee_testutils.create_test_user("test2@example.org")
        attendee2 = Attendee.objects.create(user=user2, event=event)

        form = TalkAddReservationForm(attendee=attendee1, talk=talk, data={})
        form.full_clean()
        reservation1 = form.save()
        self.assertFalse(reservation1.is_waiting)
        self.assertFalse(reservation1.is_confirmed)
        reservation1.is_confirmed = True
        reservation1.save()

        form = TalkAddReservationForm(attendee=attendee2, talk=talk, data={})
        form.full_clean()
        reservation2 = form.save()
        self.assertTrue(reservation2.is_waiting)
        self.assertFalse(reservation2.is_confirmed)


class TestAttendeeTalkFeedbackForm(TestCase):
    def setUp(self):
        event = event_testutils.create_test_event()
        speaker, _, _ = speaker_testutils.create_test_speaker()
        self.talk = Talk.objects.create(
            draft_speaker=speaker, event=event, title="Test Talk"
        )
        track = Track.objects.create(name="Test Track")
        self.talk.publish(track)
        user, _ = attendee_testutils.create_test_user()
        self.attendee = Attendee.objects.create(event=event, user=user)

    def test_fields(self):
        form = AttendeeTalkFeedbackForm(
            instance=mock.MagicMock(), talk=self.talk, attendee=self.attendee
        )
        self.assertListEqual(["score", "comment"], list(form.fields))

    def test_init_creates_form_helper(self):
        form = AttendeeTalkFeedbackForm(
            instance=mock.MagicMock(), talk=self.talk, attendee=self.attendee
        )
        self.assertIsInstance(form.helper, FormHelper)
        self.assertEqual(
            form.helper.form_action,
            "/{}/talk/{}/feedback/".format(self.talk.event.slug, self.talk.slug),
        )

    def test_init_creates_layout(self):
        form = AttendeeTalkFeedbackForm(
            instance=mock.MagicMock(), talk=self.talk, attendee=self.attendee
        )
        self.assertIsInstance(form.helper.layout, Layout)
        layout_fields = [name for [_, name] in form.helper.layout.get_field_names()]
        self.assertListEqual(["score", "comment"], layout_fields)
        self.assertEqual(
            len(form.helper.layout.get_layout_objects(Submit, greedy=True)), 1
        )

    def test_score_is_restricted_to_range(self):
        form = AttendeeTalkFeedbackForm(
            instance=mock.MagicMock(),
            data={"score": "10"},
            talk=self.talk,
            attendee=self.attendee,
        )
        form.full_clean()
        self.assertEqual(form.cleaned_data["score"], 5)
        form = AttendeeTalkFeedbackForm(
            instance=mock.MagicMock(),
            data={"score": "3"},
            talk=self.talk,
            attendee=self.attendee,
        )
        form.full_clean()
        self.assertEqual(form.cleaned_data["score"], 3)
