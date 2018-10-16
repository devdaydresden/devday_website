from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from django import forms
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.timezone import now

from event.models import Event
from speaker.tests import speaker_testutils
from talk.forms import (
    CreateTalkForm, EditTalkForm, TalkCommentForm, TalkForm,
    TalkSpeakerCommentForm, TalkVoteForm)
from talk.models import Talk, TalkFormat

try:
    from unittest import mock
except ImportError:  # Python 2.7 has no mock in unittest
    import mock

User = get_user_model()


class TalkFormTest(TestCase):
    def test_fields(self):
        form = TalkForm()
        self.assertListEqual(
            list(form.fields.keys()),
            ['title', 'abstract', 'remarks', 'talkformat'])

    def test_model(self):
        form = TalkForm()
        talk = form.save(commit=False)
        self.assertIsInstance(talk, Talk)

    def test_widgets(self):
        form = TalkForm()
        self.assertIsInstance(form.fields['abstract'].widget, forms.Textarea)
        self.assertIsInstance(form.fields['remarks'].widget, forms.Textarea)


class CreateTalkFormTest(TestCase):
    def test_init_creates_form_helper(self):
        speaker = mock.Mock()
        event = mock.Mock(slug='bla')
        form = CreateTalkForm(speaker=speaker, event=event)
        self.assertEqual(form.speaker, speaker)
        self.assertIsInstance(form.helper, FormHelper)
        self.assertEqual(form.helper.form_action, reverse(
            'submit_session', kwargs={'event': event.slug}))
        self.assertEqual(form.helper.form_id, 'create-talk-form')
        self.assertEqual(form.helper.field_template, 'devday/form/field.html')
        self.assertTrue(form.helper.html5_required)

    def test_init_creates_layout(self):
        speaker = mock.Mock()
        event = mock.Mock()
        form = CreateTalkForm(speaker=speaker, event=event)
        self.assertIsInstance(form.helper.layout, Layout)
        layout_fields = [name for [_, name] in
                         form.helper.layout.get_field_names()]
        self.assertEqual(len(layout_fields), 4)
        self.assertIn('title', layout_fields)
        self.assertIn('abstract', layout_fields)
        self.assertIn('remarks', layout_fields)
        self.assertIn('talkformat', layout_fields)

    def test_save(self):
        talk_format = TalkFormat.objects.create(name='A Talk', duration=60)
        event = Event.objects.create(title="Test event", slug="test_event",
                                     start_time=now(), end_time=now())
        event.talkform = talk_format
        speaker, _, password = speaker_testutils.create_test_speaker()
        form = CreateTalkForm(speaker=speaker, data={
            'title': 'Test',
            'abstract': 'Test abstract',
            'remarks': 'Test remarks',
            'talkformat': [talk_format.id],
        }, event=event)
        talk = form.save(commit=False)
        self.assertIsInstance(talk, Talk)
        self.assertEqual(talk.speaker, speaker)


class EditTalkFormTest(TestCase):
    def test_init_creates_form_helper(self):
        form = EditTalkForm()
        self.assertIsInstance(form.helper, FormHelper)
        self.assertEqual(form.helper.field_template, 'devday/form/field.html')
        self.assertTrue(form.helper.html5_required)

    def test_init_creates_layout(self):
        form = EditTalkForm()
        self.assertIsInstance(form.helper.layout, Layout)
        layout_fields = [
            name for [_, name] in form.helper.layout.get_field_names()]
        self.assertEqual(len(layout_fields), 4)
        self.assertEqual(
            layout_fields, ['title', 'abstract', 'remarks', 'talkformat'])


class TalkCommentFormTest(TestCase):
    def test_fields(self):
        form = TalkCommentForm(instance=mock.MagicMock(pk=1))
        self.assertListEqual(['comment', 'is_visible'], list(form.fields))

    def test_init_creates_form_helper(self):
        form = TalkCommentForm(instance=mock.MagicMock(pk=1))
        self.assertIsInstance(form.helper, FormHelper)
        self.assertEqual(form.fields['comment'].widget.attrs['rows'], 2)
        self.assertEqual(form.helper.form_action, '/committee/talks/1/comment/')

    def test_init_creates_layout(self):
        form = TalkCommentForm(instance=mock.MagicMock(pk=1))
        self.assertIsInstance(form.helper.layout, Layout)
        layout_fields = [name for [_, name] in
                         form.helper.layout.get_field_names()]
        self.assertListEqual(['comment', 'is_visible'], layout_fields)
        self.assertEqual(len(form.helper.layout.get_layout_objects(Submit)), 1)


class TalkSpeakerCommentFormTest(TestCase):
    def test_fields(self):
        form = TalkSpeakerCommentForm(instance=mock.MagicMock(pk=1))
        self.assertListEqual(['comment'], list(form.fields))

    def test_init_creates_form_helper(self):
        form = TalkSpeakerCommentForm(instance=mock.MagicMock(pk=1))
        self.assertIsInstance(form.helper, FormHelper)
        self.assertEqual(form.fields['comment'].widget.attrs['rows'], 2)
        self.assertEqual(form.helper.form_action,
                         '/session/speaker/talks/1/comment/')

    def test_init_creates_layout(self):
        form = TalkSpeakerCommentForm(instance=mock.MagicMock(pk=1))
        self.assertIsInstance(form.helper.layout, Layout)
        layout_fields = [name for [_, name] in
                         form.helper.layout.get_field_names()]
        self.assertListEqual(['comment'], layout_fields)
        self.assertEqual(len(form.helper.layout.get_layout_objects(Submit)), 1)


class TalkVoteFormTest(TestCase):
    def test_fields(self):
        form = TalkVoteForm()
        self.assertListEqual(['score'], list(form.fields))
