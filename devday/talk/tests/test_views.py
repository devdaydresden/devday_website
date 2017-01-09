import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest
from django.test import TestCase
from django.utils.translation import ugettext as _
from django_file_form.forms import ExistingFile

from attendee.models import Attendee
from talk.forms import CreateSpeakerForm, BecomeSpeakerForm, TalkCommentForm
from talk.models import Speaker, Talk, Vote, TalkComment
from talk.views import CreateTalkView, ExistingFileView, SpeakerProfileView, CreateSpeakerView

User = get_user_model()


class TestSubmitSessionView(TestCase):
    def test_submit_session_anonymous(self):
        response = self.client.get(u'/session/submit-session/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(u'talk/submit_session.html')

    def test_submit_session_user(self):
        User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(u'/session/submit-session/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(u'talk/submit_session.html')

    def test_submit_session_attendee(self):
        user = User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        Attendee.objects.create(user=user)
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(u'/session/submit-session/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(u'talk/submit_session.html')

    def test_submit_session_speaker(self):
        user = User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        attendee = Attendee.objects.create(user=user)
        Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True, shortbio=u'A short biography text')
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(u'/session/submit-session/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/session/create-session/')


class TestSpeakerRegisteredView(TestCase):
    def test_template(self):
        response = self.client.get(u'/session/speaker-registered/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'talk/speaker_registered.html')


class TestTalkSubmittedView(TestCase):
    def test_template(self):
        response = self.client.get(u'/session/submitted/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'talk/submitted.html')


class TestCreateTalkView(TestCase):
    def test_needs_login(self):
        response = self.client.get(u'/session/create-session/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/accounts/login/?next=/session/create-session/')

    def test_needs_speaker_not_user(self):
        User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(u'/session/create-session/')
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(u'400.html')

    def test_needs_speaker_not_attendee(self):
        user = User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        Attendee.objects.create(user=user)
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(u'/session/create-session/')
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(u'400.html')

    def test_template(self):
        user = User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        attendee = Attendee.objects.create(user=user)
        Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True, shortbio=u'A short biography text')
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(u'/session/create-session/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'talk/create_talk.html')

    def test_get_form_kwargs(self):
        user = User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        attendee = Attendee.objects.create(user=user)
        speaker = Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True, shortbio=u'A short biography text')
        view = CreateTalkView()
        view.request = HttpRequest()
        view.request.user = user
        kwargs = view.get_form_kwargs()
        self.assertIn(u'speaker', kwargs)
        self.assertEqual(kwargs[u'speaker'], speaker)

    def test_redirect_after_success(self):
        user = User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        attendee = Attendee.objects.create(user=user)
        Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True, shortbio=u'A short biography text')
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.post(
            u'/session/create-session/',
            data={u'title': u'A fantastic session', u'abstract': u'News for nerds, stuff that matters'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/session/submitted/')


class TestEditTalkView(TestCase):
    def setUp(self):
        user = User.objects.create_user(email=u'speaker@example.org', password=u's3cr3t')
        attendee = Attendee.objects.create(user=user)
        speaker = Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True, shortbio=u'A short biography text')
        self.talk = Talk.objects.create(speaker=speaker, title=u'A nice topic', abstract=u'reasoning about a topic')

    def test_needs_login(self):
        response = self.client.get(u'/session/edit-session/{}/'.format(self.talk.id))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/accounts/login/?next=/session/edit-session/{}/'.format(self.talk.id))

    def test_needs_speaker_not_user(self):
        User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(u'/session/edit-session/{}/'.format(self.talk.id))
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(u'400.html')

    def test_needs_speaker_not_attendee(self):
        user = User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        Attendee.objects.create(user=user)
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(u'/session/edit-session/{}/'.format(self.talk.id))
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(u'400.html')

    def test_template(self):
        self.client.login(username=u'speaker@example.org', password=u's3cr3t')
        response = self.client.get(u'/session/edit-session/{}/'.format(self.talk.id))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(u'talk/talk_form.html')

    def test_redirect_after_success(self):
        self.client.login(username=u'speaker@example.org', password=u's3cr3t')
        response = self.client.post(u'/session/edit-session/{}/'.format(self.talk.id), data={
            u'title': u'A new title', u'abstract': u'Good things come to those who wait'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/speaker/profile/')


class TestExistingFileView(TestCase):
    def setUp(self):
        user = User.objects.create_user(email=u'speaker@example.org', password=u's3cr3t')
        attendee = Attendee.objects.create(user=user)
        self.speaker = Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True, shortbio=u'A short biography text',
            portrait=SimpleUploadedFile(
                name=u'testspeaker.jpg',
                content=open(os.path.join(os.path.dirname(__file__), u'mu_at_mil_house.jpg'), 'rb').read(),
                content_type=u'image/jpeg')
        )

    def test_get_form_kwargs(self):
        view = ExistingFileView(kwargs={u'id': self.speaker.id}, request=HttpRequest())
        kwargs = view.get_form_kwargs()
        self.assertIn(u'initial', kwargs)
        self.assertIn(u'uploaded_image', kwargs[u'initial'])
        self.assertIsInstance(kwargs[u'initial'][u'uploaded_image'], ExistingFile)

    def test_get_form_kwargs_no_portrait(self):
        self.speaker.portrait = None
        self.speaker.save()
        view = ExistingFileView(kwargs={u'id': self.speaker.id}, request=HttpRequest())
        kwargs = view.get_form_kwargs()
        self.assertIn(u'initial', kwargs)
        self.assertNotIn(u'uploaded_image', kwargs[u'initial'])


class TestSpeakerProfileView(TestCase):
    def setUp(self):
        user = User.objects.create_user(email=u'speaker@example.org', password=u's3cr3t')
        attendee = Attendee.objects.create(user=user)
        self.speaker = Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True, shortbio=u'A short biography text',
            portrait=SimpleUploadedFile(
                name=u'testspeaker.jpg',
                content=open(os.path.join(os.path.dirname(__file__), u'mu_at_mil_house.jpg'), 'rb').read(),
                content_type=u'image/jpeg')
        )

    def test_needs_login(self):
        response = self.client.get(u'/speaker/profile/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/accounts/login/?next=/speaker/profile/')

    def test_needs_speaker_not_user(self):
        User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(u'/speaker/profile/')
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(u'400.html')

    def test_needs_speaker_not_attendee(self):
        user = User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        Attendee.objects.create(user=user)
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(u'/speaker/profile/')
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(u'400.html')

    def test_template(self):
        self.client.login(username=u'speaker@example.org', password=u's3cr3t')
        response = self.client.get(u'/speaker/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(u'talk/speaker_profile.html')

    def test_get_context_data_no_talks(self):
        request = HttpRequest()
        request.user = self.speaker.user.user
        view = SpeakerProfileView(request=request)
        context = view.get_context_data()
        self.assertIn(u'attendee', context)
        self.assertIn(u'speaker', context)
        self.assertEqual(context[u'speaker'], self.speaker)
        self.assertIn(u'talks', context)
        self.assertEqual(len(context[u'talks']), 0)

    def test_get_context_data_with_talk(self):
        Talk.objects.create(speaker=self.speaker, title=u'Test talk', abstract=u'A tragedy of testing and errors')
        request = HttpRequest()
        request.user = self.speaker.user.user
        view = SpeakerProfileView(request=request)
        context = view.get_context_data()
        self.assertIn(u'attendee', context)
        self.assertIn(u'speaker', context)
        self.assertEqual(context[u'speaker'], self.speaker)
        self.assertIn(u'talks', context)
        self.assertEqual(len(context[u'talks']), 1)
        self.assertEqual(context[u'talks'][0].title, u'Test talk')


class TestCreateSpeakerView(TestCase):
    def test_dispatch_anonymous(self):
        response = self.client.get(u'/session/new-speaker/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(u'talk/create_speaker.html')

    def test_get_form_class_anonymous(self):
        response = self.client.get(u'/session/new-speaker/')
        self.assertIsInstance(response.context[u'form'], CreateSpeakerForm)

    def test_dispatch_user(self):
        User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(u'/session/new-speaker/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(u'talk/create_speaker.html')

    def test_get_form_class_user(self):
        User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(u'/session/new-speaker/')
        self.assertIsInstance(response.context[u'form'], BecomeSpeakerForm)

    def test_dispatch_attendee(self):
        user = User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        Attendee.objects.create(user=user)
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(u'/session/new-speaker/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(u'talk/create_speaker.html')

    def test_get_form_class_attendee(self):
        user = User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        Attendee.objects.create(user=user)
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(u'/session/new-speaker/')
        self.assertIsInstance(response.context[u'form'], BecomeSpeakerForm)

    def test_dispatch_speaker(self):
        user = User.objects.create_user(email=u'test@example.org', password=u's3cr3t')
        attendee = Attendee.objects.create(user=user)
        Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True, shortbio=u'A short biography text'
        )
        self.client.login(username=u'test@example.org', password=u's3cr3t')
        response = self.client.get(u'/session/new-speaker/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/session/speaker-registered/')

    def test_get_email_context(self):
        request = HttpRequest()
        view = CreateSpeakerView(request=request)
        context = view.get_email_context(u'test_key')
        self.assertIn(u'request', context)
        self.assertEqual(context[u'request'], request)

    def test_form_valid_anonymous(self):
        image_file = open(os.path.join(os.path.dirname(__file__), u'mu_at_mil_house.jpg'), 'rb')
        data = {
            u'email': u'speaker@example.org', u'firstname': u'Special', u'lastname': u'Tester', u'password1': u's3cr3t',
            u'password2': u's3cr3t', u'shirt_size': u'2', u'accept_contact': u'checked', u'videopermission': u'checked',
            u'shortbio': u'A guy from somewhere having something great to talk about',
            u'uploaded_image': image_file
        }
        response = self.client.post(u'/session/new-speaker/', data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/session/speaker-registered/')
        self.assertEqual(len(mail.outbox), 1)
        user = User.objects.get(email=u'speaker@example.org')
        self.assertFalse(user.is_active)
        self.assertTrue(user.check_password(u's3cr3t'))

    def test_form_valid_user(self):
        User.objects.create_user(email=u'speaker@example.org', password=u's3cr3t')
        image_file = open(os.path.join(os.path.dirname(__file__), u'mu_at_mil_house.jpg'), 'rb')
        data = {
            u'firstname': u'Special', u'lastname': u'Tester', u'shirt_size': u'2',
            u'accept_contact': u'checked', u'videopermission': u'checked',
            u'shortbio': u'A guy from somewhere having something great to talk about',
            u'uploaded_image': image_file
        }
        self.client.login(email=u'speaker@example.org', password=u's3cr3t')
        response = self.client.post(u'/session/new-speaker/', data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/session/speaker-registered/')
        self.assertEqual(len(mail.outbox), 0)

    def test_form_valid_attendee(self):
        user = User.objects.create_user(email=u'speaker@example.org', password=u's3cr3t')
        Attendee.objects.create(user=user)
        image_file = open(os.path.join(os.path.dirname(__file__), u'mu_at_mil_house.jpg'), 'rb')
        data = {
            u'firstname': u'Special', u'lastname': u'Tester', u'shirt_size': u'2',
            u'accept_contact': u'checked', u'videopermission': u'checked',
            u'shortbio': u'A guy from somewhere having something great to talk about',
            u'uploaded_image': image_file
        }
        self.client.login(email=u'speaker@example.org', password=u's3cr3t')
        response = self.client.post(u'/session/new-speaker/', data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/session/speaker-registered/')
        self.assertEqual(len(mail.outbox), 0)


class TestTalkOverView(TestCase):
    def test_needs_authentication(self):
        response = self.client.get(u'/session/committee/talks/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/accounts/login/?next=/session/committee/talks/')

    def test_needs_committee_permissions(self):
        User.objects.create_user(email=u'user@example.org', password=u's3cr3t')
        self.client.login(email=u'user@example.org', password=u's3cr3t')
        response = self.client.get(u'/session/committee/talks/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/accounts/login/?next=/session/committee/talks/')

    def test_template(self):
        user = User.objects.create_user(email=u'committee@example.org', password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.get(u'/session/committee/talks/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'talk/talk_overview.html')

    def test_get_queryset(self):
        user = User.objects.create_user(email=u'committee@example.org', password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        talk = Talk.objects.create(
            speaker=Speaker.objects.create(
                user=Attendee.objects.create(
                    user=User.objects.create_user(email=u'speaker@example.org', password=u'g3h31m')
                ),
                videopermission=True,
                shirt_size=1,
            )
        )
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.get(u'/session/committee/talks/')
        talks = list(response.context[u'talk_list'])
        self.assertIn(talk, talks)
        self.assertTrue(hasattr(talks[0], 'average_score'))
        self.assertTrue(hasattr(talks[0], 'comment_count'))


class TestTalkDetails(TestCase):
    def setUp(self):
        self.talk = Talk.objects.create(
            speaker=Speaker.objects.create(
                user=Attendee.objects.create(
                    user=User.objects.create_user(email=u'speaker@example.org', password=u'g3h31m')
                ),
                videopermission=True,
                shirt_size=1,
            )
        )
        self.url = u'/session/committee/talks/{0:d}/'.format(self.talk.pk)

    def test_needs_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_committee_permissions(self):
        User.objects.create_user(email=u'user@example.org', password=u's3cr3t')
        self.client.login(email=u'user@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/accounts/login/?next={0:s}'.format(self.url))

    def test_template(self):
        user = User.objects.create_user(email=u'committee@example.org', password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'talk/talk_details.html')

    def test_get_queryset(self):
        user = User.objects.create_user(email=u'committee@example.org', password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.talk, response.context['talk'])
        self.assertTrue(hasattr(response.context['talk'], 'average_score'))

    def test_get_context_data_unvoted(self):
        user = User.objects.create_user(email=u'committee@example.org', password=u's3cr3t')
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
        user = User.objects.create_user(email=u'committee@example.org', password=u's3cr3t')
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
                    user=User.objects.create_user(email=u'speaker@example.org', password=u'g3h31m')
                ),
                videopermission=True,
                shirt_size=1,
            ), title=u'I have something important to say'
        )
        self.url = u'/session/committee/talks/{0:d}/comment/'.format(self.talk.pk)

    def test_needs_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_committee_permissions(self):
        User.objects.create_user(email=u'user@example.org', password=u's3cr3t')
        self.client.login(email=u'user@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_post(self):
        user = User.objects.create_user(email=u'committee@example.org', password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_form_invalid_sets_message(self):
        user = User.objects.create_user(email=u'committee@example.org', password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/session/committee/talks/{0:d}/'.format(self.talk.pk))
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level_tag, 'warning')
        self.assertIn(u'comment', messages[0].message)
        self.assertIn(_('This field is required.'), messages[0].message)

    def test_form_valid_redirects_to_talk_details(self):
        user = User.objects.create_user(email=u'committee@example.org', password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.post(self.url, data={u'comment': u'A little comment for you'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/session/committee/talks/{0:d}/'.format(self.talk.pk))
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        comments = list(response.context['comments'])
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].comment, u'A little comment for you')
        self.assertFalse(comments[0].is_visible)
        self.assertEqual(comments[0].commenter, user)

    def test_visible_comment_triggers_mail_to_speaker(self):
        user = User.objects.create_user(email=u'committee@example.org', password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.post(self.url, data={
            u'comment': u'A little comment for you', u'is_visible': u'checked'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/session/committee/talks/{0:d}/'.format(self.talk.pk))
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        comments = list(response.context['comments'])
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].comment, u'A little comment for you')
        self.assertTrue(comments[0].is_visible)
        self.assertEqual(comments[0].commenter, user)
        self.assertEqual(len(mail.outbox), 1)
        speaker_mail = mail.outbox[0]
        self.assertIn(self.talk.speaker.user.user.email, speaker_mail.recipients())
        self.assertIn(self.talk.title, speaker_mail.subject)
        self.assertIn(self.talk.title, speaker_mail.body)


class TestTalkVote(TestCase):
    def setUp(self):
        self.talk = Talk.objects.create(
            speaker=Speaker.objects.create(
                user=Attendee.objects.create(
                    user=User.objects.create_user(email=u'speaker@example.org', password=u'g3h31m')
                ),
                videopermission=True,
                shirt_size=1,
            )
        )
        self.url = u'/session/committee/talks/{0:d}/vote/'.format(self.talk.pk)

    def test_needs_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_committee_permissions(self):
        User.objects.create_user(email=u'user@example.org', password=u's3cr3t')
        self.client.login(email=u'user@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_post(self):
        user = User.objects.create_user(email=u'committee@example.org', password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_form_invalid_returns_json_error(self):
        user = User.objects.create_user(email=u'committee@example.org', password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode('utf8'),
            {u'message': u'error', u'errors': {u'score': [_(u'This field is required.')]}})

    def test_form_valid_returns_json(self):
        user = User.objects.create_user(email=u'committee@example.org', password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.post(self.url, data={'score': 4})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf8'), {u'message': u'ok'})
        votes = list(self.talk.vote_set.all())
        self.assertEqual(len(votes), 1)
        self.assertEqual(votes[0].score, 4)
        self.assertEqual(votes[0].voter, user)

    def test_second_post_updates_vote(self):
        user = User.objects.create_user(email=u'committee@example.org', password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.post(self.url, data={'score': 4})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf8'), {u'message': u'ok'})
        response = self.client.post(self.url, data={'score': 3})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf8'), {u'message': u'ok'})
        votes = list(self.talk.vote_set.all())
        self.assertEqual(len(votes), 1)
        self.assertEqual(votes[0].score, 3)
        self.assertEqual(votes[0].voter, user)


class TestTalkVoteClear(TestCase):
    def setUp(self):
        self.talk = Talk.objects.create(
            speaker=Speaker.objects.create(
                user=Attendee.objects.create(
                    user=User.objects.create_user(email=u'speaker@example.org', password=u'g3h31m')
                ),
                videopermission=True,
                shirt_size=1,
            )
        )
        self.url = u'/session/committee/talks/{0:d}/vote/clear/'.format(self.talk.pk)

    def test_needs_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_committee_permissions(self):
        User.objects.create_user(email=u'user@example.org', password=u's3cr3t')
        self.client.login(email=u'user@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_post(self):
        user = User.objects.create_user(email=u'committee@example.org', password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_post_returns_json(self):
        user = User.objects.create_user(email=u'committee@example.org', password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf8'), {u'message': u'vote deleted'})

    def test_post_deletes_vote(self):
        user = User.objects.create_user(email=u'committee@example.org', password=u's3cr3t')
        user.groups.add(Group.objects.get(name=u'talk_committee'))
        vote = self.talk.vote_set.create(voter=user, score=3)
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertRaises(Vote.DoesNotExist, Vote.objects.get, pk=vote.pk)


class TestTalkCommentDelete(TestCase):
    def setUp(self):
        self.talk = Talk.objects.create(
            speaker=Speaker.objects.create(
                user=Attendee.objects.create(
                    user=User.objects.create_user(email=u'speaker@example.org', password=u'g3h31m')
                ),
                videopermission=True,
                shirt_size=1,
            )
        )
        self.user = User.objects.create_user(email=u'committee@example.org', password=u's3cr3t')
        self.user.groups.add(Group.objects.get(name=u'talk_committee'))
        self.talk_comment = self.talk.talkcomment_set.create(
            commenter=self.user, comment='A little anoying comment', is_visible=False)
        self.url = u'/session/committee/talks/delete_comment/{0:d}/'.format(self.talk_comment.pk)

    def test_needs_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_committee_permissions(self):
        User.objects.create_user(email=u'user@example.org', password=u's3cr3t')
        self.client.login(email=u'user@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_post(self):
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_delete_of_other_users_comments_rejected(self):
        member2 = User.objects.create_user(email=u'committee2@example.org', password=u's3cr3t')
        member2.groups.add(Group.objects.get(name=u'talk_committee'))
        self.client.login(email=u'committee2@example.org', password=u's3cr3t')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)

    def test_post_returns_json_response(self):
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf8'), {u'message': u'comment deleted'})

    def test_post_deletes_comment(self):
        self.client.login(email=u'committee@example.org', password=u's3cr3t')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertRaises(TalkComment.DoesNotExist, TalkComment.objects.get, pk=self.talk_comment.pk)
