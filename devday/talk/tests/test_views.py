import errno
import os
import shutil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django_file_form.forms import ExistingFile
from django.http import HttpRequest
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils.translation import ugettext as _

from attendee.models import Attendee
from devday.utils.devdata import DevData
from event.models import Event
from event.tests.testutils import create_test_event, update_current_event
from talk.forms import (CreateSpeakerForm, BecomeSpeakerForm, TalkCommentForm,
                        EditTalkForm, TalkSpeakerCommentForm)
from talk.models import Speaker, Talk, TalkFormat, TalkComment, Vote, Track
from talk.views import CreateTalkView, ExistingFileView, CreateSpeakerView

User = get_user_model()


class TestSubmitSessionView(TestCase):
    def setUp(self):
        update_current_event(registration_open=True, submission_open=True)

    def test_submit_session_anonymous(self):
        response = self.client.get(u'/session/submit-session/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(u'talk/submit_session.html')

    def test_submit_session_user(self):
        User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        with override_settings(TALK_SUBMISSION_OPEN=True):  # FIXME _OPEN
            response = self.client.get(u'/session/submit-session/')
            self.assertRedirects(response, u'/session/create-session/', 302,
                                 fetch_redirect_response=False)

    def test_submit_session_attendee(self):
        user = User.objects.create_user(email=u'test@example.org',
                                        password=u's3cr3t')
        event = Event.objects.current_event()
        Attendee.objects.create(user=user, event=event)
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(u'/session/submit-session/')
        self.assertRedirects(response, u'/session/create-session/', 302,
                             fetch_redirect_response=False)

    def test_submit_session_speaker(self):
        user = User.objects.create_user(email=u'test@example.org',
                                        password=u's3cr3t')
        event = Event.objects.current_event()
        attendee = Attendee.objects.create(user=user, event=event)
        Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True,
            shortbio=u'A short biography text')
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(u'/session/submit-session/')
        self.assertRedirects(response, u'/session/create-session/', 302)


class TestSpeakerRegisteredView(TestCase):
    def test_template(self):
        response = self.client.get(u'/session/speaker-registered/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'talk/speaker_registered.html')


class TestTalkSubmittedView(TestCase):
    def setUp(self):
        self.url = u'/session/submitted/'

    def test_needs_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/accounts/login/?next={}'.format(self.url))

    def test_needs_speaker_not_user(self):
        User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/session/new-speaker/')

    def test_needs_speaker_not_attendee(self):
        user = User.objects.create_user(email=u'test@example.org',
                                        password=u's3cr3t')
        event = Event.objects.current_event()
        Attendee.objects.create(user=user, event=event)
        self.client.login(username=u'test@example.org',
                          password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/session/new-speaker/')

    def test_template(self):
        user = User.objects.create_user(email=u'speaker@example.org',
                                        password=u's3cr3t')
        event = Event.objects.current_event()
        attendee = Attendee.objects.create(user=user, event=event)
        speaker = Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True,
            shortbio=u'A short biography text')
        self.client.login(email=u'speaker@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'talk/submitted.html')
        self.assertIn(
            u'"/speaker/profile/{0:d}/"'.format(speaker.pk),
            response.content.decode('utf8'))

    def test_get_context_data(self):
        user = User.objects.create_user(email=u'speaker@example.org',
                                        password=u's3cr3t')
        event = Event.objects.current_event()
        attendee = Attendee.objects.create(user=user, event=event)
        speaker = Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True,
            shortbio=u'A short biography text')
        self.client.login(email=u'speaker@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(u'speaker', response.context)
        self.assertEqual(response.context[u'speaker'], speaker)


class TestCreateTalkView(TestCase):
    def setUp(self):
        self.url = u'/session/create-session/'
        update_current_event(registration_open=True, submission_open=True)

    def test_redirect_if_talk_submission_closed(self):
        update_current_event(submission_open=False)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/session/submission-closed/')

    def test_needs_login(self):
        update_current_event(submission_open=True)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/accounts/login/?next={}'.format(self.url))

    def test_needs_speaker_not_user(self):
        User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/session/new-speaker/')

    def test_needs_speaker_not_attendee(self):
        user = User.objects.create_user(email=u'test@example.org',
                                        password=u's3cr3t')
        Attendee.objects.create(user=user, event=create_test_event())
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/session/new-speaker/')

    def test_template(self):
        user = User.objects.create_user(email=u'test@example.org',
                                        password=u's3cr3t')
        event = Event.objects.current_event()
        attendee = Attendee.objects.create(user=user, event=event)
        Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True,
            shortbio=u'A short biography text')
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'talk/create_talk.html')

    def test_get_form_kwargs(self):
        user = User.objects.create_user(email=u'test@example.org',
                                        password=u's3cr3t')
        event = Event.objects.current_event()
        attendee = Attendee.objects.create(user=user, event=event)
        speaker = Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True,
            shortbio=u'A short biography text')
        view = CreateTalkView()
        view.request = HttpRequest()
        view.request.user = user
        kwargs = view.get_form_kwargs()
        self.assertIn(u'speaker', kwargs)
        self.assertEqual(kwargs[u'speaker'], speaker)

    def test_redirect_after_success(self):
        user = User.objects.create_user(email=u'test@example.org',
                                        password=u's3cr3t')
        event = Event.objects.current_event()
        talkformat = TalkFormat.objects.create(name='A Talk', duration=60)
        event.talkformat.add(talkformat)
        attendee = Attendee.objects.create(user=user, event=event)
        Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True,
            shortbio=u'A short biography text')
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.post(
            self.url,
            data={u'title': u'A fantastic session',
                  u'abstract': u'News for nerds, stuff that matters',
                  u'talkformat': [talkformat.id]})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/session/submitted/')


class TestExistingFileView(TestCase):
    def setUp(self):
        user = User.objects.create_user(email=u'speaker@example.org',
                                        password=u's3cr3t')
        attendee = Attendee.objects.create(user=user,
                                           event=create_test_event())
        self.speaker = Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True,
            shortbio=u'A short biography text',
            portrait=SimpleUploadedFile(
                name=u'testspeaker.jpg',
                content=open(
                    os.path.join(os.path.dirname(__file__),
                                 u'mu_at_mil_house.jpg'), 'rb').read(),
                content_type=u'image/jpeg')
        )

    def test_get_form_kwargs(self):
        view = ExistingFileView(kwargs={u'id': self.speaker.id},
                                request=HttpRequest())
        kwargs = view.get_form_kwargs()
        self.assertIn(u'initial', kwargs)
        self.assertIn(u'uploaded_image', kwargs[u'initial'])
        self.assertIsInstance(kwargs[u'initial'][u'uploaded_image'],
                              ExistingFile)

    def test_get_form_kwargs_no_portrait(self):
        self.speaker.portrait = None
        self.speaker.save()
        view = ExistingFileView(kwargs={u'id': self.speaker.id},
                                request=HttpRequest())
        kwargs = view.get_form_kwargs()
        self.assertIn(u'initial', kwargs)
        self.assertNotIn(u'uploaded_image', kwargs[u'initial'])


class TestSpeakerProfileView(TestCase):
    def setUp(self):
        user = User.objects.create_user(email=u'speaker@example.org',
                                        password=u's3cr3t')
        self.event = Event.objects.current_event()
        attendee = Attendee.objects.create(user=user, event=self.event)
        self.speaker = Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True,
            shortbio=u'A short biography text',
            portrait=SimpleUploadedFile(
                name=u'testspeaker.jpg',
                content=open(
                    os.path.join(os.path.dirname(__file__),
                                 u'mu_at_mil_house.jpg'), 'rb').read(),
                content_type=u'image/jpeg')
        )
        self.url = u'/speaker/profile/{0:d}/'.format(self.speaker.pk)

    def test_needs_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_speaker_not_user(self):
        User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/session/new-speaker/')

    def test_needs_speaker_not_attendee(self):
        user = User.objects.create_user(email=u'test@example.org',
                                        password=u's3cr3t')
        Attendee.objects.create(user=user, event=self.event)
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/session/new-speaker/')

    def test_template(self):
        self.client.login(username=u'speaker@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(u'talk/speaker_profile.html')

    def test_get_context_data_no_talks(self):
        self.client.login(username=u'speaker@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertIn(u'attendee', context)
        self.assertIn(u'speaker', context)
        self.assertEqual(context[u'speaker'], self.speaker)
        self.assertIn(u'talks', context)
        self.assertEqual(len(context[u'talks']), 0)

    def test_get_context_data_with_talk(self):
        Talk.objects.create(speaker=self.speaker, title=u'Test talk',
                            abstract=u'A tragedy of testing and errors')
        self.client.login(username=u'speaker@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertIn(u'attendee', context)
        self.assertIn(u'speaker', context)
        self.assertEqual(context[u'speaker'], self.speaker)
        self.assertIn(u'talks', context)
        self.assertEqual(len(context[u'talks']), 1)
        self.assertEqual(context[u'talks'][0].title, u'Test talk')

    def test_submit_changes_data(self):
        Talk.objects.create(speaker=self.speaker, title=u'Test talk',
                            abstract=u'A tragedy of testing and errors')
        self.client.login(username=u'speaker@example.org', password=u's3cr3t')
        response = self.client.post(self.url, data={
            'videopermission': 'checked',
            'shortbio': 'A nice guy from high above the sky',
            'shirt_size': 4,
        })
        self.assertEqual(response.status_code, 302)
        self.speaker.refresh_from_db()
        self.assertEqual(self.speaker.shortbio,
                         'A nice guy from high above the sky')


class TestCreateSpeakerView(TestCase):
    def setUp(self):
        self.url = u'/session/new-speaker/'

    @classmethod
    def setUpTestData(cls):
        cls.devdata = DevData()
        cls.devdata.create_talk_formats()
        cls.devdata.update_events()

    def test_redirect_if_talk_submission_closed(self):
        update_current_event(submission_open=False)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/session/submission-closed/')

    def test_dispatch_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(u'talk/create_speaker.html')

    def test_get_form_class_anonymous(self):
        response = self.client.get(self.url)
        self.assertIsInstance(response.context[u'form'], CreateSpeakerForm)

    def test_dispatch_user(self):
        User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(u'talk/create_speaker.html')

    def test_get_form_class_user(self):
        User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertIsInstance(response.context[u'form'], BecomeSpeakerForm)

    def test_dispatch_attendee(self):
        user = User.objects.create_user(email=u'test@example.org',
                                        password=u's3cr3t')
        Attendee.objects.create(user=user, event=create_test_event())
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(u'talk/create_speaker.html')

    def test_get_form_class_attendee(self):
        user = User.objects.create_user(email=u'test@example.org',
                                        password=u's3cr3t')
        Attendee.objects.create(user=user, event=create_test_event())
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertIsInstance(response.context[u'form'], BecomeSpeakerForm)

    def test_dispatch_speaker(self):
        user = User.objects.create_user(email=u'test@example.org',
                                        password=u's3cr3t')
        attendee = Attendee.objects.create(user=user,
                                           event=create_test_event())
        Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True,
            shortbio=u'A short biography text'
        )
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context[u'form'], BecomeSpeakerForm)

    def test_get_email_context(self):
        request = HttpRequest()
        # noinspection PyArgumentList,PyArgumentList
        view = CreateSpeakerView(request=request)
        context = view.get_email_context(u'test_key')
        self.assertIn(u'request', context)
        self.assertEqual(context[u'request'], request)

    def test_form_valid_anonymous(self):
        image_file = open(
            os.path.join(os.path.dirname(__file__), u'mu_at_mil_house.jpg'),
            'rb')
        data = {
            u'email': u'speaker@example.org', u'firstname': u'Special',
            u'lastname': u'Tester', u'password1': u's3cr3t',
            u'password2': u's3cr3t', u'shirt_size': u'2',
            u'accept_contact': u'checked', u'videopermission': u'checked',
            u'shortbio': u'A guy from somewhere having something great'
                         u' to talk about',
            u'phone': '+49-351-28200815', u'uploaded_image': image_file
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/session/speaker-registered/')
        self.assertEqual(len(mail.outbox), 1)
        user = User.objects.get(email=u'speaker@example.org')
        self.assertFalse(user.is_active)
        self.assertTrue(user.check_password(u's3cr3t'))

    def test_form_valid_user(self):
        User.objects.create_user(email=u'speaker@example.org',
                                 password=u's3cr3t')
        image_file = open(
            os.path.join(os.path.dirname(__file__),
                         u'mu_at_mil_house.jpg'), 'rb')
        data = {
            u'firstname': u'Special', u'lastname': u'Tester',
            u'shirt_size': u'2', u'accept_contact': u'checked',
            u'videopermission': u'checked',
            u'shortbio': u'A guy from somewhere having something great',
            u'uploaded_image': image_file
        }
        self.client.login(email=u'speaker@example.org', password=u's3cr3t')
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/session/create-session/')
        self.assertEqual(len(mail.outbox), 0)

    def test_form_valid_attendee(self):
        user = User.objects.create_user(email=u'speaker@example.org',
                                        password=u's3cr3t')
        Attendee.objects.create(user=user, event=create_test_event())
        image_file = open(
            os.path.join(os.path.dirname(__file__),
                         u'mu_at_mil_house.jpg'), 'rb')
        data = {
            u'firstname': u'Special', u'lastname': u'Tester',
            u'shirt_size': u'2', u'accept_contact': u'checked',
            u'videopermission': u'checked',
            u'shortbio': u'A guy from somewhere having something great',
            u'phone': u'+49-351-28200815', u'uploaded_image': image_file
        }
        self.client.login(email=u'speaker@example.org', password=u's3cr3t')
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/session/create-session/')
        self.assertEqual(len(mail.outbox), 0)


class TestTalkOverView(TestCase):
    def test_needs_authentication(self):
        response = self.client.get(u'/committee/talks/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/accounts/login/?next=/committee/talks/')

    def test_needs_committee_permissions(self):
        User.objects.create_user(email=u'user@example.org', password=u's3cr3t')
        self.client.login(email=u'user@example.org', password=u's3cr3t')
        response = self.client.get(u'/committee/talks/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/accounts/login/?next=/committee/talks/')

    def test_template(self):
        user = User.objects.create_user(email=u'committee@example.org',
                                        password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.get(u'/committee/talks/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'talk/talk_committee_overview.html')

    def test_get_queryset(self):
        user = User.objects.create_user(email=u'committee@example.org',
                                        password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        event = Event.objects.current_event()
        talk = Talk.objects.create(
            speaker=Speaker.objects.create(
                user=Attendee.objects.create(
                    user=User.objects.create_user(email=u'speaker@example.org',
                                                  password=u'g3h31m'),
                    event=event
                ),
                videopermission=True,
                shirt_size=1,
            )
        )
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.get(u'/committee/talks/')
        talks = list(response.context[u'talk_list'])
        self.assertIn(talk, talks)
        self.assertTrue(hasattr(talks[0], 'average_score'))
        self.assertTrue(hasattr(talks[0], 'comment_count'))

    def test_get_queryset_sorting(self):
        user = User.objects.create_user(email=u'committee@example.org',
                                        password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        event = Event.objects.current_event()
        speaker1 = Speaker.objects.create(
            user=Attendee.objects.create(
                user=User.objects.create_user(first_name=u'Frodo',
                                              email=u'speaker@example.org',
                                              password=u'g3h31m'),
                event=event
            ),
            videopermission=True,
            shirt_size=1,
        )
        speaker2 = Speaker.objects.create(
            user=Attendee.objects.create(
                user=User.objects.create_user(first_name=u'Bilbo',
                                              email=u'speaker2@example.org',
                                              password=u'g3h31m'),
                event=event
            ),
            videopermission=True,
            shirt_size=1,
        )
        talk1 = Talk.objects.create(speaker=speaker1, title=u'Test Session 1')
        talk2 = Talk.objects.create(speaker=speaker2, title=u'Test Session 2')
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.get(u'/committee/talks/')
        talks = list(response.context[u'talk_list'])
        self.assertListEqual([talk1, talk2], talks)
        response = self.client.get(
            u'/committee/talks/?sort_order=speaker&sort_dir=asc')
        talks = list(response.context[u'talk_list'])
        self.assertListEqual([talk2, talk1], talks)
        response = self.client.get(
            u'/committee/talks/?sort_order=title&sort_dir=desc')
        talks = list(response.context[u'talk_list'])
        self.assertListEqual([talk2, talk1], talks)


class TestTalkDetails(TestCase):
    def setUp(self):
        self.talk = Talk.objects.create(
            speaker=Speaker.objects.create(
                user=Attendee.objects.create(
                    user=User.objects.create_user(email=u'speaker@example.org',
                                                  password=u'g3h31m'),
                    event=create_test_event()
                ),
                videopermission=True,
                shirt_size=1,
            )
        )
        self.url = u'/committee/talks/{0:d}/'.format(self.talk.pk)

    def test_needs_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_committee_permissions(self):
        User.objects.create_user(email=u'user@example.org', password=u's3cr3t')
        self.client.login(email=u'user@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/accounts/login/?next={0:s}'.format(self.url))

    def test_template(self):
        user = User.objects.create_user(email=u'committee@example.org',
                                        password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'talk/talk_committee_details.html')

    def test_get_queryset(self):
        user = User.objects.create_user(email=u'committee@example.org',
                                        password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.talk, response.context['talk'])
        self.assertTrue(hasattr(response.context['talk'], 'average_score'))

    def test_get_context_data_unvoted(self):
        user = User.objects.create_user(email=u'committee@example.org',
                                        password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertIsInstance(context['comment_form'], TalkCommentForm)
        self.assertIsNone(context['user_vote'])
        self.assertIn('average_votes', context)
        self.assertIn('comments', context)

    def test_get_context_data_voted(self):
        user = User.objects.create_user(email=u'committee@example.org',
                                        password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.talk.vote_set.create(voter=user, score=3)
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertIsInstance(context['comment_form'], TalkCommentForm)
        self.assertEqual(context['user_vote'], 3)
        self.assertIn('average_votes', context)
        self.assertIn('comments', context)


class TestSubmitTalkComment(TestCase):
    def setUp(self):
        self.talk = Talk.objects.create(
            speaker=Speaker.objects.create(
                user=Attendee.objects.create(
                    user=User.objects.create_user(email=u'speaker@example.org',
                                                  password=u'g3h31m'),
                    event=create_test_event()
                ),
                videopermission=True,
                shirt_size=1,
            ), title=u'I have something important to say'
        )
        self.url = u'/committee/talks/{0:d}/comment/'.format(self.talk.pk)

    def test_needs_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_committee_permissions(self):
        User.objects.create_user(email=u'user@example.org', password=u's3cr3t')
        self.client.login(email=u'user@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_post(self):
        user = User.objects.create_user(email=u'committee@example.org',
                                        password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_form_invalid_sets_message(self):
        user = User.objects.create_user(email=u'committee@example.org',
                                        password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/committee/talks/{0:d}/'.format(self.talk.pk))
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        messages = list(response.context[u'messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level_tag, u'warning')
        self.assertIn(u'comment', messages[0].message)
        self.assertIn(_(u'This field is required.'), messages[0].message)

    def test_form_valid_redirects_to_talk_details(self):
        user = User.objects.create_user(email=u'committee@example.org',
                                        password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.post(
            self.url, data={u'comment': u'A little comment for you'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/committee/talks/{0:d}/'.format(self.talk.pk))
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        comments = list(response.context[u'comments'])
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].comment, u'A little comment for you')
        self.assertFalse(comments[0].is_visible)
        self.assertEqual(comments[0].commenter, user)

    def test_visible_comment_triggers_mail_to_speaker(self):
        user = User.objects.create_user(email=u'committee@example.org',
                                        password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.post(self.url, data={
            u'comment': u'A little comment for you',
            u'is_visible': u'checked'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/committee/talks/{0:d}/'.format(self.talk.pk))
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        comments = list(response.context[u'comments'])
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].comment, u'A little comment for you')
        self.assertTrue(comments[0].is_visible)
        self.assertEqual(comments[0].commenter, user)
        self.assertEqual(len(mail.outbox), 1)
        speaker_mail = mail.outbox[0]
        self.assertIn(self.talk.speaker.user.user.email,
                      speaker_mail.recipients())
        self.assertIn(self.talk.title, speaker_mail.subject)
        self.assertIn(self.talk.title, speaker_mail.body)


class TestTalkVote(TestCase):
    def setUp(self):
        self.event = Event.objects.current_event()
        self.talk = Talk.objects.create(
            speaker=Speaker.objects.create(
                user=Attendee.objects.create(
                    user=User.objects.create_user(email=u'speaker@example.org',
                                                  password=u'g3h31m'),
                    event=self.event
                ),
                videopermission=True,
                shirt_size=1,
            )
        )
        self.url = u'/committee/talks/{0:d}/vote/'.format(self.talk.pk)

    def test_needs_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_committee_permissions(self):
        User.objects.create_user(email=u'user@example.org', password=u's3cr3t')
        self.client.login(email=u'user@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_post(self):
        user = User.objects.create_user(email=u'committee@example.org',
                                        password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_form_invalid_returns_json_error(self):
        user = User.objects.create_user(email=u'committee@example.org',
                                        password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode('utf8'),
            {u'message': u'error',
             u'errors': {u'score': [_(u'This field is required.')]}})

    def test_form_valid_returns_json(self):
        user = User.objects.create_user(email=u'committee@example.org',
                                        password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.post(self.url, data={'score': 4})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf8'),
                             {u'message': u'ok'})
        votes = list(self.talk.vote_set.all())
        self.assertEqual(len(votes), 1)
        self.assertEqual(votes[0].score, 4)
        self.assertEqual(votes[0].voter, user)

    def test_second_post_updates_vote(self):
        user = User.objects.create_user(email=u'committee@example.org',
                                        password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.post(self.url, data={'score': 4})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf8'),
                             {u'message': u'ok'})
        response = self.client.post(self.url, data={'score': 3})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf8'),
                             {u'message': u'ok'})
        votes = list(self.talk.vote_set.all())
        self.assertEqual(len(votes), 1)
        self.assertEqual(votes[0].score, 3)
        self.assertEqual(votes[0].voter, user)


class TestTalkVoteClear(TestCase):
    def setUp(self):
        self.event = Event.objects.current_event()
        self.talk = Talk.objects.create(
            speaker=Speaker.objects.create(
                user=Attendee.objects.create(
                    user=User.objects.create_user(email=u'speaker@example.org',
                                                  password=u'g3h31m'),
                    event=self.event
                ),
                videopermission=True,
                shirt_size=1,
            )
        )
        self.url = u'/committee/talks/{0:d}/vote/clear/'.format(self.talk.pk)

    def test_needs_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_committee_permissions(self):
        User.objects.create_user(email=u'user@example.org', password=u's3cr3t')
        self.client.login(email=u'user@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_post(self):
        user = User.objects.create_user(email=u'committee@example.org',
                                        password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_post_returns_json(self):
        user = User.objects.create_user(email=u'committee@example.org',
                                        password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf8'),
                             {u'message': u'vote deleted'})

    def test_post_deletes_vote(self):
        user = User.objects.create_user(email=u'committee@example.org',
                                        password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        vote = self.talk.vote_set.create(voter=user, score=3)
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertRaises(Vote.DoesNotExist, Vote.objects.get, pk=vote.pk)


class TestTalkCommentDelete(TestCase):
    def setUp(self):
        self.event = Event.objects.current_event()
        self.talk = Talk.objects.create(
            speaker=Speaker.objects.create(
                user=Attendee.objects.create(
                    user=User.objects.create_user(email=u'speaker@example.org',
                                                  password=u'g3h31m'),
                    event=self.event
                ),
                videopermission=True,
                shirt_size=1,
            )
        )
        self.user = User.objects.create_user(email=u'committee@example.org',
                                             password=u's3cr3t')
        self.user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.talk_comment = self.talk.talkcomment_set.create(
            commenter=self.user, comment=u'A little anoying comment',
            is_visible=False)
        self.url = u'/committee/talks/{0:d}/delete_comment/' \
            .format(self.talk_comment.pk)

    def test_needs_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_committee_permissions(self):
        User.objects.create_user(email=u'user@example.org', password=u's3cr3t')
        self.client.login(email=u'user@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_post(self):
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_delete_of_other_users_comments_rejected(self):
        member2 = User.objects.create_user(email=u'committee2@example.org',
                                           password=u's3cr3t')
        member2.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee2@example.org', password=u's3cr3t')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)

    def test_post_returns_json_response(self):
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf8'),
                             {u'message': u'comment deleted'})

    def test_post_deletes_comment(self):
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertRaises(TalkComment.DoesNotExist, TalkComment.objects.get,
                          pk=self.talk_comment.pk)


class TestSpeakerTalkDetails(TestCase):
    def setUp(self):
        self.event = Event.objects.current_event()
        self.speaker = Speaker.objects.create(
            user=Attendee.objects.create(
                user=User.objects.create_user(email=u'speaker@example.org',
                                              password=u's3cr3t'),
                event=self.event,
            ),
            videopermission=True, shirt_size=1,
        )
        self.talk = Talk.objects.create(
            speaker=self.speaker, title=u'Something important',
            abstract=u'I have something important to say')
        self.committee_member = User.objects.create_user(
            email=u'committee@example.org', password=u'g3h31m')
        self.committee_member.groups.add(
            Group.objects.get(name=u'talk_committee'))
        self.comment = self.talk.talkcomment_set.create(
            commenter=self.committee_member,
            comment=u'Is this really important?', is_visible=True)
        self.url = '/session/speaker/talks/{0:d}/'.format(self.talk.pk)

    def test_needs_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_speaker(self):
        User.objects.create_user(email=u'user@example.org', password=u's3cr3t')
        self.client.login(email=u'user@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/session/new-speaker/'.format(self.url))

    def test_needs_talk_speaker(self):
        Speaker.objects.create(
            user=Attendee.objects.create(
                user=User.objects.create_user(email=u'other@example.org',
                                              password=u's3cr3t'),
                event=self.event
            ),
            videopermission=True, shirt_size=1,
        )
        self.client.login(email=u'other@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_template(self):
        self.client.login(email=u'speaker@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(u'talk/talk_speaker_details.html')

    def test_form_class(self):
        self.client.login(email=u'speaker@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], EditTalkForm)

    def test_get_context_data(self):
        other_comment = self.talk.talkcomment_set.create(
            commenter=self.committee_member, comment=u'Committee eyes only',
            is_visible=False)
        self.client.login(email=u'speaker@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        comments = list(context[u'comments'])
        self.assertEqual(len(comments), 1)
        self.assertIn(self.comment, comments)
        self.assertNotIn(other_comment, comments)
        self.assertIsInstance(context[u'comment_form'], TalkSpeakerCommentForm)

    def test_changes_session_data(self):
        self.client.login(email=u'speaker@example.org', password=u's3cr3t')
        talkformat, created = TalkFormat.objects.get_or_create(name='A Talk',
                                                               duration=60)
        response = self.client.post(self.url, data={
            u'title': u'A good talk',
            u'abstract': u'This is a really good talk',
            u'talkformat': [talkformat.id],
        })
        self.assertEqual(response.status_code, 302)
        self.talk.refresh_from_db()
        self.assertEqual(self.talk.title, u'A good talk')
        self.assertEqual(self.talk.abstract, u'This is a really good talk')

    def test_success_redirects_to_talk_details(self):
        self.client.login(email=u'speaker@example.org', password=u's3cr3t')
        talkformat, created = TalkFormat.objects.get_or_create(name='A Talk',
                                                               duration=60)
        response = self.client.post(self.url, data={
            u'title': u'A good talk',
            u'abstract': u'This is a really good talk',
            u'talkformat': [talkformat.id],
        })
        self.assertRedirects(response, self.url, status_code=302)


class TestSubmitTalkSpeakerComment(TestCase):
    def setUp(self):
        self.event = Event.objects.current_event()
        self.speaker = Speaker.objects.create(
            user=Attendee.objects.create(
                user=User.objects.create_user(email=u'speaker@example.org',
                                              password=u's3cr3t'),
                event=self.event
            ),
            videopermission=True, shirt_size=1,
        )
        self.talk = Talk.objects.create(
            speaker=self.speaker, title=u'Something important',
            abstract=u'I have something important to say')
        self.url = u'/session/speaker/talks/{0:d}/comment/' \
            .format(self.talk.pk)

    def test_needs_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_speaker(self):
        User.objects.create_user(email=u'user@example.org', password=u's3cr3t')
        self.client.login(email=u'user@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/session/new-speaker/'.format(self.url))

    def test_needs_talk_speaker(self):
        Speaker.objects.create(
            user=Attendee.objects.create(
                user=User.objects.create_user(email=u'other@example.org',
                                              password=u's3cr3t'),
                event=self.event
            ),
            videopermission=True, shirt_size=1,
        )
        self.client.login(email=u'other@example.org', password=u's3cr3t')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)

    def test_needs_post(self):
        self.client.login(email=u'speaker@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_form_invalid_sets_message(self):
        self.client.login(email=u'speaker@example.org', password=u's3cr3t')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/session/speaker/talks/{0:d}/'.format(self.talk.pk))
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        messages = list(response.context[u'messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level_tag, u'warning')
        self.assertIn(u'comment', messages[0].message)
        self.assertIn(_(u'This field is required.'), messages[0].message)

    def test_form_valid_redirects_to_talk_details(self):
        self.client.login(email=u'speaker@example.org', password=u's3cr3t')
        response = self.client.post(
            self.url, data={u'comment': u'A little comment for you'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/session/speaker/talks/{0:d}/'.format(self.talk.pk))
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        comments = list(response.context[u'comments'])
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].comment, u'A little comment for you')
        self.assertTrue(comments[0].is_visible)
        self.assertEqual(comments[0].commenter, self.speaker.user.user)


class TestTalkSpeakerCommentDelete(TestCase):
    def setUp(self):
        self.event = Event.objects.current_event()
        self.speaker = Speaker.objects.create(
            user=Attendee.objects.create(
                user=User.objects.create_user(email=u'speaker@example.org',
                                              password=u's3cr3t'),
                event=self.event
            ),
            videopermission=True, shirt_size=1,
        )
        self.talk = Talk.objects.create(
            speaker=self.speaker, title=u'Something important',
            abstract=u'I have something important to say')
        self.talk_comment = self.talk.talkcomment_set.create(
            commenter=self.speaker.user.user,
            comment='A little anoying comment', is_visible=True)
        self.url = u'/session/speaker/talks/delete_comment/{0:d}/' \
            .format(self.talk_comment.pk)

    def test_needs_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_post(self):
        self.client.login(email=u'speaker@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_needs_speaker(self):
        User.objects.create_user(email=u'user@example.org', password=u's3cr3t')
        self.client.login(email=u'user@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         u'/session/new-speaker/'.format(self.url))

    def test_needs_talk_speaker(self):
        Speaker.objects.create(
            user=Attendee.objects.create(
                user=User.objects.create_user(email=u'other@example.org',
                                              password=u's3cr3t'),
                event=self.event
            ),
            videopermission=True, shirt_size=1,
        )
        self.client.login(email=u'other@example.org', password=u's3cr3t')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)

    def test_post_returns_json_response(self):
        self.client.login(email=u'speaker@example.org', password=u's3cr3t')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf8'),
                             {u'message': u'comment deleted'})

    def test_post_deletes_comment(self):
        self.client.login(email=u'speaker@example.org', password=u's3cr3t')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertRaises(TalkComment.DoesNotExist, TalkComment.objects.get,
                          pk=self.talk_comment.pk)


class TestSpeakerPublic(TestCase):
    def setUp(self):
        self.event = Event.objects.current_event()
        speaker_placeholder_file = 'icons8-contacts-26.png'
        speaker_placeholder_source_path = os.path.join(
            settings.STATICFILES_DIRS[0], 'img', speaker_placeholder_file)
        speaker_portrait_media_dir = 'speakers'
        self.speaker_portrait_media_path = os.path.join(
            speaker_portrait_media_dir, speaker_placeholder_file)
        speaker_portrait_dir = os.path.join(settings.MEDIA_ROOT,
                                            speaker_portrait_media_dir)
        speaker_portrait_path = os.path.join(settings.MEDIA_ROOT,
                                             self.speaker_portrait_media_path)
        self.speaker = Speaker.objects.create(
            user=Attendee.objects.create(
                user=User.objects.create_user(
                    email=u'speaker@example.org',
                    password=u's3cr3t'),
                event=self.event
            ),
            videopermission=True, shirt_size=1,
        )
        if not os.path.isfile(speaker_portrait_path):
            try:
                os.makedirs(speaker_portrait_dir)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            shutil.copyfile(speaker_placeholder_source_path,
                            speaker_portrait_path)
        self.speaker.portrait = self.speaker.portrait.field \
            .attr_class(self.speaker, self.speaker.portrait.field,
                        self.speaker_portrait_media_path)
        self.speaker.save()
        self.track = Track.objects.create(event=self.event, name='Track 1')
        self.talk = Talk.objects.create(
            speaker=self.speaker, title=u'Something important',
            abstract=u'I have something important to say',
            track=self.track)

    def test_template_used(self):
        response = self.client.get(
            '/session/speaker/{}/'.format(self.speaker.id))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'talk/speaker_public.html')

    def test_speaker_with_two_talks(self):
        Talk.objects.create(
            speaker=self.speaker, title=u'Some other talk',
            abstract='Been there, done that',
            track=self.track)
        response = self.client.get(
            '/session/speaker/{}/'.format(self.speaker.id))
        self.assertEqual(response.status_code, 200)

    def test_context_has_speaker(self):
        response = self.client.get(
            '/session/speaker/{}/'.format(self.speaker.id))
        self.assertIn('speaker', response.context)
        self.assertEqual(response.context['speaker'], self.speaker)

    def test_context_has_talk(self):
        response = self.client.get(
            '/session/speaker/{}/'.format(self.speaker.id))
        self.assertIn('talks', response.context)
        self.assertEqual(list(response.context['talks']), [self.talk])

    def test_context_has_all_talks(self):
        talk2 = Talk.objects.create(
            speaker=self.speaker, title=u'Some other talk',
            abstract='Been there, done that',
            track=self.track)
        response = self.client.get(
            '/session/speaker/{}/'.format(self.speaker.id))
        self.assertIn('talks', response.context)
        self.assertEqual(
            set(response.context['talks']), {self.talk, talk2})


class TestTalkListView(TestCase):
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

        cls.url = '/{}/talk/'.format(cls.event.slug)

    def test_talklistview(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.title)

    def test_talklistpreviewview(self):
        response = self.client.get(reverse(
            'session_list_preview',
            kwargs={'event': self.event.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.title)
