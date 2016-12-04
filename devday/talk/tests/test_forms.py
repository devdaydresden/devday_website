from django import forms
from django.test import SimpleTestCase
from django.test import TransactionTestCase

from talk.forms import TalkForm, SpeakerForm
from talk.models import Talk


class TalkFormTest(TransactionTestCase):
    def test_fields(self):
        form = TalkForm()
        self.assertListEqual(
            list(form.fields.keys()), ['title', 'abstract', 'remarks'])

    def test_model(self):
        form = TalkForm()
        talk = form.save(commit=False)
        self.assertIsInstance(talk, Talk)

    def test_widgets(self):
        form = TalkForm()
        self.assertIsInstance(form.fields['abstract'].widget, forms.Textarea)
        self.assertIsInstance(form.fields['remarks'].widget, forms.Textarea)


class SpeakerFormTest(TransactionTestCase):
    def test_fields(self):
        form = SpeakerForm()
        self.assertListEqual(
            list(form.fields.keys()),
            ['shortbio', 'videopermission', 'shirt_size', 'firstname',
             'lastname', 'uploaded_image', 'form_id', 'upload_url',
             'delete_url']
        )


class ExistingFileFormTest(SimpleTestCase):
    pass


class DevDayRegistrationFormTest(SimpleTestCase):
    pass


class CreateTalkFormTest(SimpleTestCase):
    pass


class TalkAuthenticationFormTest(SimpleTestCase):
    pass


class BecomeSpeakerFormTest(SimpleTestCase):
    pass


class CreateSpeakerFormTest(SimpleTestCase):
    pass
