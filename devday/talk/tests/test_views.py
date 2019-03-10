from datetime import datetime
from xml.etree import ElementTree

from django.contrib.auth.models import Group
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import ugettext as _

from attendee.models import Attendee
from attendee.tests import attendee_testutils
from devday.utils.devdata import DevData
from event.models import Event
from event.tests import event_testutils
from speaker.tests import speaker_testutils
from talk import COMMITTEE_GROUP
from talk.forms import (EditTalkForm, TalkCommentForm, TalkSpeakerCommentForm)
from talk.models import (
    AttendeeVote, Talk, TalkComment, TalkFormat, TalkMedia, Track, Vote)
# noinspection PyUnresolvedReferences
from talk.tests import talk_testutils


# noinspection PyUnresolvedReferences
class LoginTestMixin(object):
    def login_user(self, email='test@example.org'):
        _, password = attendee_testutils.create_test_user(email)
        self.client.login(username=email, password=password)

    def login_speaker(self, email='speaker@example.org', **kwargs):
        speaker, user, password = speaker_testutils.create_test_speaker(
            email, **kwargs)
        self.client.login(username=email, password=password)
        return speaker, user

    def login_committee_member(self, email='committee@example.org'):
        user, password = attendee_testutils.create_test_user(email)
        user.groups.add(Group.objects.get(name=COMMITTEE_GROUP))
        self.client.login(email=email, password=password)
        return user


class TestPrepareSubmitSessionView(LoginTestMixin, TestCase):
    def setUp(self):
        self.event = event_testutils.create_test_event('Test event')
        self.email = 'test@example.org'
        self.url = '/session/{}/prepare-submit/'.format(self.event.slug)

    def test_submit_session_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('talk/prepare_prepare_submit_session.html')

    def test_submit_session_user(self):
        self.login_user()
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            '/speaker/register/?next=/session/{}/create-session/'.format(
                self.event.slug), 302, fetch_redirect_response=False)

    def test_submit_session_speaker(self):
        self.login_speaker()
        response = self.client.get(self.url)
        self.assertRedirects(
            response, '/session/{}/create-session/'.format(self.event.slug),
            302, fetch_redirect_response=False)


class TestTalkSubmittedView(LoginTestMixin, TestCase):
    def setUp(self):
        self.event = event_testutils.create_test_event()
        self.url = '/session/{}/submitted/'.format(self.event.slug)
        self.email = 'speaker@example.org'

    def test_needs_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/accounts/login/?next={}'.format(self.url))

    def test_needs_speaker_not_user(self):
        self.login_user()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/speaker/register/?next={}'.format(self.url))

    def test_template(self):
        speaker, _ = self.login_speaker()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'talk/submitted.html')
        self.assertIn('"/speaker/profile/"', response.content.decode('utf8'))

    def test_get_context_data(self):
        speaker, _ = self.login_speaker()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('speaker', response.context)
        self.assertEqual(response.context['speaker'], speaker)


class TestCreateTalkView(LoginTestMixin, TestCase):
    def setUp(self):
        self.email = 'test@example.org'
        self.event = event_testutils.create_test_event('Test event')
        self.url = '/session/{}/create-session/'.format(self.event.slug)

    def test_redirect_if_talk_submission_closed(self):
        event_testutils.update_event(self.event, submission_open=False)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/session/submission-closed/')

    def test_needs_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/accounts/login/?next={}'.format(self.url))

    def test_needs_speaker_not_user(self):
        self.login_user()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/speaker/register/?next={}'.format(self.url))

    def test_template(self):
        self.login_speaker(short_biography='A short biography text')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'talk/talk_form.html')

    def test_redirect_after_success(self):
        talk_format = TalkFormat.objects.create(name='A Talk', duration=60)
        self.event.talkformat.add(talk_format)

        speaker, _ = self.login_speaker(
            short_biography='A short biography text')
        response = self.client.post(
            self.url, data={
                'title': 'A fantastic session',
                'abstract': 'News for nerds, stuff that matters',
                'talkformat': [talk_format.id],
                'event': self.event.id,
                'draft_speaker': speaker.id,
            })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/session/{}/submitted/'.format(self.event.slug))


class TestTalkOverView(LoginTestMixin, TestCase):
    def setUp(self):
        self.url = '/committee/talks/'

    def test_needs_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/accounts/login/?next={}'.format(self.url))

    def test_needs_committee_permissions(self):
        self.login_user()
        response = self.client.get('/committee/talks/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/accounts/login/?next={}'.format(self.url))

    def test_template(self):
        self.login_committee_member()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'talk/talk_committee_overview.html')

    def test_get_queryset(self):
        event = Event.objects.current_event()
        speaker, _, _ = speaker_testutils.create_test_speaker()
        talk = Talk.objects.create(draft_speaker=speaker, event=event)

        self.login_committee_member()
        response = self.client.get(self.url)
        talks = list(response.context['talk_list'])
        self.assertIn(talk, talks)
        self.assertTrue(hasattr(talks[0], 'average_score'))
        self.assertTrue(hasattr(talks[0], 'comment_count'))

    def test_get_queryset_sorting(self):
        event = Event.objects.current_event()
        speaker1, _, _ = speaker_testutils.create_test_speaker(
            email='frodo@example.org', name='Frodo')
        speaker2, _, _ = speaker_testutils.create_test_speaker(
            email='bilbo@example.org', name='Bilbo')
        talk1 = Talk.objects.create(
            draft_speaker=speaker1, title='Test Session 1', event=event)
        talk2 = Talk.objects.create(
            draft_speaker=speaker2, title='Test Session 2', event=event)

        self.login_committee_member()
        response = self.client.get(self.url)
        talks = list(response.context['talk_list'])
        self.assertListEqual([talk1, talk2], talks)
        response = self.client.get(
            '{}?sort_order=speaker&sort_dir=asc'.format(self.url))
        talks = list(response.context['talk_list'])
        self.assertListEqual([talk2, talk1], talks)
        response = self.client.get(
            '{}?sort_order=title&sort_dir=desc'.format(self.url))
        talks = list(response.context['talk_list'])
        self.assertListEqual([talk2, talk1], talks)


class TestTalkDetails(TestCase):
    def setUp(self):
        speaker, _, _ = speaker_testutils.create_test_speaker()
        self.event = event_testutils.create_test_event()
        self.talk = Talk.objects.create(
            draft_speaker=speaker, event=self.event, title='Test Talk')
        track = Track.objects.create(name='Test Track')
        self.talk.publish(track)
        self.url = '/{}/talk/{}/'.format(self.event.slug, self.talk.slug)

    def test_needs_no_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'talk/talk_details.html')

    def test_get_context_data(self):
        response = self.client.get(self.url)
        self.assertIn('speaker', response.context)
        self.assertIn('event', response.context)
        self.assertEqual(
            response.context['speaker'], self.talk.published_speaker)
        self.assertEqual(response.context['event'], self.event)


class TestCommitteeTalkDetails(TestCase):
    def setUp(self):
        speaker, _, _ = speaker_testutils.create_test_speaker()
        event = event_testutils.create_test_event()
        self.talk = Talk.objects.create(draft_speaker=speaker, event=event)
        self.url = '/committee/talks/{0:d}/'.format(self.talk.pk)

    def test_needs_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_committee_permissions(self):
        email = 'user@example.org'
        _, password = attendee_testutils.create_test_user(email)
        self.client.login(email=email, password=password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/accounts/login/?next={0:s}'.format(self.url))

    def test_template(self):
        committee_email = 'committee@example.org'
        user, password = attendee_testutils.create_test_user(committee_email)
        user.groups.add(Group.objects.get(name=COMMITTEE_GROUP))
        self.client.login(email=committee_email, password=password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'talk/talk_committee_details.html')

    def test_get_queryset(self):
        committee_email = 'committee@example.org'
        user, password = attendee_testutils.create_test_user(committee_email)
        user.groups.add(Group.objects.get(name=COMMITTEE_GROUP))
        self.client.login(email=committee_email, password=password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.talk, response.context['talk'])
        self.assertTrue(hasattr(response.context['talk'], 'average_score'))

    def test_get_context_data_unvoted(self):
        committee_email = 'committee@example.org'
        user, password = attendee_testutils.create_test_user(committee_email)
        user.groups.add(Group.objects.get(name=COMMITTEE_GROUP))
        self.client.login(email=committee_email, password=password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertIsInstance(context['comment_form'], TalkCommentForm)
        self.assertIsNone(context['user_vote'])
        self.assertIn('average_votes', context)
        self.assertIn('comments', context)

    def test_get_context_data_voted(self):
        committee_email = 'committee@example.org'
        user, password = attendee_testutils.create_test_user(committee_email)
        user.groups.add(Group.objects.get(name=COMMITTEE_GROUP))
        self.talk.vote_set.create(voter=user, score=3)
        self.client.login(email=committee_email, password=password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertIsInstance(context['comment_form'], TalkCommentForm)
        self.assertEqual(context['user_vote'], 3)
        self.assertIn('average_votes', context)
        self.assertIn('comments', context)


class TestSubmitTalkComment(TestCase):
    def setUp(self):
        speaker, _, _ = speaker_testutils.create_test_speaker()
        event = event_testutils.create_test_event()
        self.talk = Talk.objects.create(
            draft_speaker=speaker, event=event,
            title='I have something important to say')
        self.url = '/committee/talks/{0:d}/comment/'.format(self.talk.pk)

    def test_needs_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_committee_permissions(self):
        email = 'user@example.org'
        _, password = attendee_testutils.create_test_user(email)
        self.client.login(email=email, password=password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_post(self):
        committee_email = 'committee@example.org'
        user, password = attendee_testutils.create_test_user(committee_email)
        user.groups.add(Group.objects.get(name=COMMITTEE_GROUP))
        self.client.login(email=committee_email, password=password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_form_invalid_sets_message(self):
        committee_email = 'committee@example.org'
        user, password = attendee_testutils.create_test_user(committee_email)
        user.groups.add(Group.objects.get(name=COMMITTEE_GROUP))
        self.client.login(email=committee_email, password=password)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/committee/talks/{0:d}/'.format(self.talk.pk))
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level_tag, 'warning')
        self.assertIn('comment', messages[0].message)
        self.assertIn(_('This field is required.'), messages[0].message)

    def test_form_valid_redirects_to_talk_details(self):
        committee_email = 'committee@example.org'
        user, password = attendee_testutils.create_test_user(committee_email)
        user.groups.add(Group.objects.get(name=COMMITTEE_GROUP))
        self.client.login(email=committee_email, password=password)
        response = self.client.post(
            self.url, data={'comment': 'A little comment for yo'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         '/committee/talks/{0:d}/'.format(self.talk.pk))
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        comments = list(response.context['comments'])
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].comment, 'A little comment for yo')
        self.assertFalse(comments[0].is_visible)
        self.assertEqual(comments[0].commenter, user)

    def test_visible_comment_triggers_mail_to_speaker(self):
        committee_email = 'committee@example.org'
        user, password = attendee_testutils.create_test_user(committee_email)
        user.groups.add(Group.objects.get(name=COMMITTEE_GROUP))
        self.client.login(email=committee_email, password=password)
        response = self.client.post(self.url, data={
            'comment': 'A little comment for yo',
            'is_visible': 'checked'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/committee/talks/{0:d}/'.format(self.talk.pk))
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        comments = list(response.context['comments'])
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].comment, 'A little comment for yo')
        self.assertTrue(comments[0].is_visible)
        self.assertEqual(comments[0].commenter, user)
        self.assertEqual(len(mail.outbox), 1)
        speaker_mail = mail.outbox[0]
        self.assertIn(
            self.talk.draft_speaker.user.email, speaker_mail.recipients())
        self.assertIn(self.talk.title, speaker_mail.subject)
        self.assertIn(self.talk.title, speaker_mail.body)


class TestTalkVote(LoginTestMixin, TestCase):
    def setUp(self):
        speaker, _, _ = speaker_testutils.create_test_speaker()
        self.event = event_testutils.create_test_event()
        self.talk = Talk.objects.create(
            draft_speaker=speaker, event=self.event,
            title='I have something important to say')
        self.url = '/committee/talks/{0:d}/vote/'.format(self.talk.pk)

    def test_needs_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         '/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_committee_permissions(self):
        email = 'user@example.org'
        _, password = attendee_testutils.create_test_user(email)
        self.client.login(email=email, password=password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         '/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_post(self):
        self.login_committee_member()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_form_invalid_returns_json_error(self):
        self.login_committee_member()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode('utf8'),
            {'message': 'error',
             'errors': {'score': [_('This field is required.')]}})

    def test_form_valid_returns_json(self):
        user = self.login_committee_member()
        response = self.client.post(self.url, data={'score': 4})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf8'),
                             {'message': 'ok'})
        votes = list(self.talk.vote_set.all())
        self.assertEqual(len(votes), 1)
        self.assertEqual(votes[0].score, 4)
        self.assertEqual(votes[0].voter, user)

    def test_second_post_updates_vote(self):
        user = self.login_committee_member()
        response = self.client.post(self.url, data={'score': 4})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf8'),
                             {'message': 'ok'})
        response = self.client.post(self.url, data={'score': 3})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf8'),
                             {'message': 'ok'})
        votes = list(self.talk.vote_set.all())
        self.assertEqual(len(votes), 1)
        self.assertEqual(votes[0].score, 3)
        self.assertEqual(votes[0].voter, user)


class TestTalkVoteClear(LoginTestMixin, TestCase):
    def setUp(self):
        self.event = event_testutils.create_test_event()
        speaker, _, _ = speaker_testutils.create_test_speaker()
        self.talk = Talk.objects.create(
            draft_speaker=speaker, event=self.event)
        self.url = '/committee/talks/{0:d}/vote/clear/'.format(self.talk.pk)

    def test_needs_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_committee_permissions(self):
        self.login_user()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         '/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_post(self):
        self.login_committee_member()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_post_returns_json(self):
        self.login_committee_member()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf8'),
                             {'message': 'vote deleted'})

    def test_post_deletes_vote(self):
        user = self.login_committee_member()
        vote = self.talk.vote_set.create(voter=user, score=3)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertRaises(Vote.DoesNotExist, Vote.objects.get, pk=vote.pk)


class TestTalkCommentDelete(LoginTestMixin, TestCase):
    def setUp(self):
        self.event = event_testutils.create_test_event()
        speaker, _, _ = speaker_testutils.create_test_speaker()
        self.talk = Talk.objects.create(draft_speaker=speaker, event=self.event)
        self.user, self.password = attendee_testutils.create_test_user(
            'committee@example.org')
        self.user.groups.add(Group.objects.get(name=COMMITTEE_GROUP))
        self.talk_comment = self.talk.talkcomment_set.create(
            commenter=self.user, comment='A little annoying comment',
            is_visible=False)
        self.url = '/committee/talks/{0:d}/delete_comment/' \
            .format(self.talk_comment.pk)

    def test_needs_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_committee_permissions(self):
        self.login_user()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_post(self):
        self.client.login(email=self.user.email, password=self.password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_delete_of_other_users_comments_rejected(self):
        self.login_committee_member('committee2@example.org')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)

    def test_post_returns_json_response(self):
        self.client.login(email=self.user.email, password=self.password)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode('utf8'),
                             {'message': 'comment deleted'})

    def test_post_deletes_comment(self):
        self.client.login(email=self.user.email, password=self.password)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertRaises(TalkComment.DoesNotExist, TalkComment.objects.get,
                          pk=self.talk_comment.pk)


class TestSpeakerTalkDetails(LoginTestMixin, TestCase):
    def setUp(self):
        self.event = event_testutils.create_test_event()
        self.speaker, self.user, self.password = (
            speaker_testutils.create_test_speaker())
        self.talk = Talk.objects.create(
            draft_speaker=self.speaker, title='Something important',
            event=self.event, abstract='I have something important to say')
        self.committee_member, _ = attendee_testutils.create_test_user(
            email='committee@example.org')
        self.committee_member.groups.add(
            Group.objects.get(name=COMMITTEE_GROUP))
        self.comment = self.talk.talkcomment_set.create(
            commenter=self.committee_member,
            comment='Is this really important?', is_visible=True)
        self.url = '/session/speaker/talks/{0:d}/'.format(self.talk.pk)

    def test_needs_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_speaker(self):
        self.login_user()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/speaker/register/?next={}'.format(self.url))

    def test_needs_talk_speaker(self):
        self.login_speaker('other@example.org')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_template(self):
        self.client.login(email=self.user.email, password=self.password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('talk/talk_speaker_details.html')

    def test_form_class(self):
        self.client.login(email=self.user.email, password=self.password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], EditTalkForm)

    def test_get_context_data(self):
        other_comment = self.talk.talkcomment_set.create(
            commenter=self.committee_member, comment='Committee eyes only',
            is_visible=False)
        self.client.login(email=self.user.email, password=self.password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        comments = list(context['comments'])
        self.assertEqual(len(comments), 1)
        self.assertIn(self.comment, comments)
        self.assertNotIn(other_comment, comments)
        self.assertIsInstance(context['comment_form'], TalkSpeakerCommentForm)

    def test_changes_session_data(self):
        self.client.login(email=self.user.email, password=self.password)
        talk_format, created = TalkFormat.objects.get_or_create(
            name='A Talk', duration=60)
        response = self.client.post(self.url, data={
            'title': 'A good talk',
            'abstract': 'This is a really good talk',
            'talkformat': [talk_format.id],
        })
        self.assertEqual(response.status_code, 302)
        self.talk.refresh_from_db()
        self.assertEqual(self.talk.title, 'A good talk')
        self.assertEqual(self.talk.abstract, 'This is a really good talk')

    def test_success_redirects_to_talk_details(self):
        self.client.login(email=self.user.email, password=self.password)
        talkformat, created = TalkFormat.objects.get_or_create(
            name='A Talk', duration=60)
        response = self.client.post(self.url, data={
            'title': 'A good talk',
            'abstract': 'This is a really good talk',
            'talkformat': [talkformat.id],
        })
        self.assertRedirects(response, self.url, status_code=302)


class TestSubmitTalkSpeakerComment(LoginTestMixin, TestCase):
    def setUp(self):
        self.event = event_testutils.create_test_event()
        self.speaker, self.user, self.password = (
            speaker_testutils.create_test_speaker())
        self.talk = Talk.objects.create(
            draft_speaker=self.speaker, title='Something important',
            abstract='I have something important to say', event=self.event)
        self.url = '/session/speaker/talks/{0:d}/comment/'.format(
            self.talk.pk)

    def test_needs_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_speaker(self):
        self.login_user()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/speaker/register/?next={0:s}'.format(self.url))

    def test_needs_talk_speaker(self):
        self.login_speaker('other@example.org')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)

    def test_needs_post(self):
        self.client.login(email=self.user.email, password=self.password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_form_invalid_sets_message(self):
        self.client.login(email=self.user.email, password=self.password)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/session/speaker/talks/{0:d}/'.format(self.talk.pk))
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level_tag, 'warning')
        self.assertIn('comment', messages[0].message)
        self.assertIn(_('This field is required.'), messages[0].message)

    def test_form_valid_redirects_to_talk_details(self):
        self.client.login(email=self.user.email, password=self.password)
        response = self.client.post(
            self.url, data={'comment': 'A little comment for yo'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/session/speaker/talks/{0:d}/'.format(self.talk.pk))
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        comments = list(response.context['comments'])
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].comment, 'A little comment for yo')
        self.assertTrue(comments[0].is_visible)
        self.assertEqual(comments[0].commenter, self.speaker.user)


class TestTalkSpeakerCommentDelete(LoginTestMixin, TestCase):
    def setUp(self):
        self.event = event_testutils.create_test_event()
        self.speaker, self.user, self.password = (
            speaker_testutils.create_test_speaker())
        self.talk = Talk.objects.create(
            draft_speaker=self.speaker, title='Something important',
            abstract='I have something important to say',
            event=self.event)
        self.talk_comment = self.talk.talkcomment_set.create(
            commenter=self.speaker.user,
            comment='A little annoying comment', is_visible=True)
        self.url = '/session/speaker/talks/delete_comment/{0:d}/'.format(
            self.talk_comment.pk)

    def test_needs_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/accounts/login/?next={0:s}'.format(self.url))

    def test_needs_speaker(self):
        self.login_user()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/speaker/register/?next={0:s}'.format(self.url))

    def test_needs_post(self):
        self.client.login(email=self.user.email, password=self.password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_post_returns_json_response(self):
        self.client.login(email=self.user.email, password=self.password)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode('utf8'), {'message': 'comment deleted'})

    def test_post_deletes_comment(self):
        self.client.login(email=self.user.email, password=self.password)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertRaises(
            TalkComment.DoesNotExist, TalkComment.objects.get,
            pk=self.talk_comment.pk)


class TestRedirectVideoView(TestCase):
    def test_redirects_to_current_event_video_list(self):
        response = self.client.get('/videos/')
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, '/{}/videos/'.format(
            Event.objects.current_event().slug))


class TestTalkListView(TestCase):
    @classmethod
    def setUpTestData(cls):
        # TODO: think about not using DevData here
        #  we don't need all of its functionality and could generate a sample
        #  session grid for a synthetic event instead
        cls.event = Event.objects.current_event()
        cls.event.registration_open = False
        cls.event.submission_open = False
        devdata = DevData()
        devdata.create_talk_formats()
        standard_format = TalkFormat.objects.get(name='Vortrag', duration=60)
        cls.event.talkformat.add(standard_format)
        cls.event.save()
        # we need to create more users because of the stochastic
        # subsampling for attendees
        devdata.create_users_and_attendees(
            amount=devdata.SPEAKERS_PER_EVENT * 2, events=[cls.event])
        devdata.create_speakers(events=[cls.event])
        devdata.create_talks(events=[cls.event])
        devdata.create_tracks(events=[cls.event])
        devdata.create_rooms(events=[cls.event])
        devdata.create_time_slots(events=[cls.event])
        devdata.create_talk_slots(events=[cls.event])

        cls.url = '/{}/'.format(cls.event.slug)

    def test_talk_list_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.title)

    def test_inactive_event(self):
        event = event_testutils.create_test_event('Unpublished')
        event.published = False
        event.save()
        response = self.client.get('/{}/'.format(event.slug))
        self.assertEquals(response.status_code, 404)

    def test_talk_list_preview_view(self):
        response = self.client.get(reverse(
            'session_list_preview',
            kwargs={'event': self.event.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.title)

    def test_infobeamer_xml_view(self):
        response = self.client.get(reverse(
            'infobeamer', kwargs={'event': self.event.slug}))
        self.assertEqual(response.status_code, 200)
        root = ElementTree.fromstring(response.content)
        self.assertEquals(root.tag, 'schedule')
        self.assertEquals(
            root.find('./conference/title').text,
            self.event.title)
        self.assertEquals(len(root.findall('day/room')), 4)
        self.assertEquals(len(root.findall('day/room/event')), 14)

    def test_infobeamer_xml_view_with_starttoday(self):
        response = self.client.get(reverse(
            'infobeamer', kwargs={'event': self.event.slug}),
            data={'starttoday': ''})
        self.assertEqual(response.status_code, 200)
        root = ElementTree.fromstring(response.content)
        self.assertEquals(root.tag, 'schedule')
        self.assertEquals(
            root.find('./conference/title').text,
            self.event.title)
        self.assertEquals(len(root.findall('day/room')), 4)
        self.assertEquals(len(root.findall('day/room/event')), 14)
        start_date = datetime.strptime(
            root.find('./conference/start').text, '%Y-%m-%d')
        start_time = root.find('./day').attrib['start']
        talk_start_time = root.find('./day/room/event/date').text
        # workaround for Python < 3.7 that cannot parse time zone information
        # with colon
        start_time = datetime.strptime(
            start_time[:-3] + start_time[-2:], '%Y-%m-%dT%H:%M:%S%z')
        talk_start_time = datetime.strptime(
            talk_start_time[:-3] + talk_start_time[-2:], '%Y-%m-%dT%H:%M:%S%z')
        today = datetime.today().date()
        self.assertEquals(today, start_date.date())
        self.assertEqual(today, start_time.date())
        self.assertEqual(today, talk_start_time.date())

    def test_infobeamer_xml_view_skips_unscheduled_session(self):
        test_speaker, _, _ = speaker_testutils.create_test_speaker(
            'unscheduled@example.org', 'Unscheduled Talk Speaker')
        unscheduled_session = talk_testutils.create_test_talk(
            test_speaker, self.event)
        unscheduled_session.title = 'Unscheduled'
        unscheduled_session.slug = 'unscheduled'
        unscheduled_session.save()
        track = Track.objects.create(event=self.event, name='Test Track')
        unscheduled_session.publish(track)
        response = self.client.get(reverse(
            'infobeamer', kwargs={'event': self.event.slug}))
        self.assertEqual(response.status_code, 200)
        root = ElementTree.fromstring(response.content)
        self.assertEquals(root.tag, 'schedule')
        self.assertEquals(len(root.findall('day/room/event')), 14)

    def test_infobeamer_xml_view_skips_unused_room(self):
        self.event.room_set.create(name='Besenkammer')
        response = self.client.get(reverse(
            'infobeamer', kwargs={'event': self.event.slug}))
        self.assertEqual(response.status_code, 200)
        root = ElementTree.fromstring(response.content)
        self.assertEquals(root.tag, 'schedule')
        self.assertEquals(len(root.findall('day/room')), 4)

    def test_legacy_list_url(self):
        response = self.client.get(self.url + 'talk/')
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, self.url)

    def test_talk_archive_list_view(self):
        event = Event.objects.all_but_current().first()
        response = self.client.get('/{}/'.format(event.slug))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, event.title)

    def test_talk_list_with_unscheduled(self):
        test_speaker, _, _ = speaker_testutils.create_test_speaker(
            'unscheduled@example.org', 'Unscheduled Talk Speaker')
        unscheduled_session = talk_testutils.create_test_talk(
            test_speaker, self.event)
        unscheduled_session.title = 'Unscheduled'
        unscheduled_session.slug = 'unscheduled'
        unscheduled_session.save()
        track = Track.objects.create(event=self.event, name='Test Track')
        unscheduled_session.publish(track)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('unscheduled', response.context)
        self.assertTemplateUsed(response, "talk/talk_grid.html")
        self.assertTemplateUsed(response, "talk/talk_list_entry.html")
        self.assertIn(unscheduled_session, response.context['unscheduled'])


class TestInfoBeamerXMLView(TestCase):
    def test_unspecified_event_redirects_to_current(self):
        response = self.client.get('/schedule.xml')
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse(
            'infobeamer',
            kwargs={'event': Event.objects.current_event().slug}))


class TestTalkVideoView(TestCase):
    def setUp(self):
        self.event = event_testutils.create_test_event()
        self.url = '/{}/videos/'.format(self.event.slug)

    def test_anonymous_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'talk/talk_videos.html')

    def test_context_data(self):
        response = self.client.get(self.url)
        self.assertIn('event', response.context)
        self.assertEqual(response.context['event'], self.event)

    def test_render_with_talks(self):
        speaker1, _, _ = speaker_testutils.create_test_speaker(
            email='testspeaker1@example.org', name='Test Speaker 1')
        speaker2, _, _ = speaker_testutils.create_test_speaker(
            email='testspeaker2@example.org', name='Test Speaker 2')
        talk1 = Talk.objects.create(
            draft_speaker=speaker1, title='Talk 1', event=self.event)
        talk2 = Talk.objects.create(
            draft_speaker=speaker2, title='Talk 2', event=self.event)
        track = Track.objects.create(name='Things')
        talk1.publish(track)
        talk2.publish(track)
        TalkMedia.objects.create(
            talk=talk1, codelink='https://example.org/git/talk1code')
        TalkMedia.objects.create(
            talk=talk2, codelink='https://example.org/git/talk1code')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('event', response.context)
        self.assertEqual(response.context['event'], self.event)
        self.assertIn('talk_list', response.context)
        self.assertIn(talk1, response.context['talk_list'])
        self.assertIn(talk2, response.context['talk_list'])


class TestEventSessionSummaryView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff, cls.staff_password = attendee_testutils.create_test_user(
            email='staff@example.org', is_staff=True)
        cls.user, cls.user_password = attendee_testutils.create_test_user()
        cls.event = Event.objects.current_event()

    def setUp(self):
        self.speaker, _, _ = speaker_testutils.create_test_speaker(
            email='testspeaker@example.org', name='Test Speaker',
            organization='Test Org')
        self.talk = Talk.objects.create(
            draft_speaker=self.speaker, title='A Talk', event=self.event
        )
        self.url = reverse('admin_csv_session_summary')

    def test_get_session_summary_anonymous(self):
        r = self.client.get(self.url)
        self.assertEquals(r.status_code, 302)
        self.assertEquals(
            r.url, '/accounts/login/?next={}'.format(self.url),
            'should redirect to login page')

    def test_get_session_summary_regular_user(self):
        self.client.login(username=self.user, password=self.user_password)
        r = self.client.get(self.url)
        self.assertEquals(r.status_code, 302)
        self.assertEquals(
            r.url, '/accounts/login/?next={}'.format(self.url),
            'should redirect to login page')

    def test_get_session_summary_staff(self):
        self.client.login(
            username=self.staff.email, password=self.staff_password)
        r = self.client.get(self.url)
        self.assertEquals(
            r.status_code, 200,
            'should retrieve data from {}'.format(self.url))
        self.assertIn(
            self.talk.title, r.content.decode(),
            'talk should be listed in session summary')


class TestAttendeeVotingView(TestCase):
    def setUp(self):
        self.event = event_testutils.create_test_event('test event')
        self.event.voting_open = True
        self.event.save()
        self.speaker, _, _ = speaker_testutils.create_test_speaker()
        self.session = talk_testutils.create_test_talk(
            self.speaker, self.event)
        self.session.title = 'Test session'
        self.session.slug = 'test-session'
        self.session.publish(Track.objects.create(name='Test track'))
        self.user, self.password = attendee_testutils.create_test_user(
            'testattendee@example.org')
        self.attendee = Attendee.objects.create(
            user=self.user, event=self.event)
        self.url = '/{}/voting/'.format(self.event.slug)

    def test_voting_view_requires_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response, '/accounts/login/?next={}'.format(self.url))

    def test_voting_template(self):
        self.client.login(username=self.user.email, password=self.password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'talk/talk_voting.html')
        self.assertIn(self.session, response.context['talk_list'])

    def test_no_unpublished_sessions_for_voting(self):
        self.client.login(username=self.user.email, password=self.password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'talk/talk_voting.html')
        unpublished = talk_testutils.create_test_talk(
            self.speaker, self.event)
        unpublished.title = 'Other session'
        unpublished.slug = 'other-session'
        unpublished.save()
        self.assertNotIn(unpublished, response.context['talk_list'])


class TestAttendeeTalkVote(TestCase):
    def setUp(self):
        self.event = event_testutils.create_test_event('test event')
        self.event.voting_open = True
        self.event.save()
        self.speaker, _, _ = speaker_testutils.create_test_speaker()
        self.talk = talk_testutils.create_test_talk(
            self.speaker, self.event)
        self.talk.title = 'Test session'
        self.talk.slug = 'test-session'
        self.talk.publish(Track.objects.create(name='Test track'))
        self.user, self.password = attendee_testutils.create_test_user(
            'testattendee@example.org')
        self.attendee = Attendee.objects.create(
            user=self.user, event=self.event)
        self.url = '/{}/submit-vote/'.format(self.event.slug)

    def test_voting_view_requires_login(self):
        response = self.client.post(
            self.url, data={'talk-id': self.talk.id})
        self.assertRedirects(
            response, '/accounts/login/?next={}'.format(self.url))

    def test_voting_requires_post(self):
        self.client.login(username=self.user.email, password=self.password)
        response = self.client.get(self.url)
        self.assertEquals(response.status_code, 405)

    def test_voting_requires_talk_id(self):
        self.client.login(username=self.user.email, password=self.password)
        response = self.client.post(
            self.url)
        self.assertEquals(response.status_code, 400)

    def test_voting_requires_score(self):
        self.client.login(username=self.user.email, password=self.password)
        response = self.client.post(
            self.url, data={'talk-id': self.talk.id})
        self.assertEquals(response.status_code, 200)
        data = response.json()
        self.assertEquals(data['message'], 'error')
        self.assertIn('score', data['errors'])

    def test_voting_creates_attendee_vote(self):
        self.client.login(username=self.user.email, password=self.password)
        response = self.client.post(
            self.url, data={'talk-id': self.talk.id, 'score': 3})
        self.assertEquals(response.status_code, 200)
        self.assertJSONEqual(response.content, {'message': 'ok'})
        vote = self.attendee.attendeevote_set.get(talk=self.talk)
        self.assertEquals(vote.score, 3)

    def test_voting_updates_existing_vote(self):
        vote = self.talk.attendeevote_set.create(
            attendee=self.attendee, score=4)
        self.client.login(username=self.user.email, password=self.password)
        response = self.client.post(
            self.url, data={'talk-id': self.talk.id, 'score': 3})
        self.assertEquals(response.status_code, 200)
        self.assertJSONEqual(response.content, {'message': 'ok'})
        vote.refresh_from_db()
        self.assertEquals(vote.score, 3)


class TestAttendeeTalkClearVote(TestCase):
    def setUp(self):
        self.event = event_testutils.create_test_event('test event')
        self.event.voting_open = True
        self.event.save()
        self.speaker, _, _ = speaker_testutils.create_test_speaker()
        self.talk = talk_testutils.create_test_talk(
            self.speaker, self.event)
        self.talk.title = 'Test session'
        self.talk.slug = 'test-session'
        self.talk.publish(Track.objects.create(name='Test track'))
        self.user, self.password = attendee_testutils.create_test_user(
            'testattendee@example.org')
        self.attendee = Attendee.objects.create(
            user=self.user, event=self.event)
        self.url = '/{}/clear-vote/'.format(self.event.slug)

    def test_clear_voting_view_requires_login(self):
        response = self.client.post(
            self.url, data={'talk-id': self.talk.id})
        self.assertRedirects(
            response, '/accounts/login/?next={}'.format(self.url))

    def test_clear_voting_requires_post(self):
        self.client.login(username=self.user.email, password=self.password)
        response = self.client.get(self.url)
        self.assertEquals(response.status_code, 405)

    def test_clear_voting_requires_talk_id(self):
        self.client.login(username=self.user.email, password=self.password)
        response = self.client.post(
            self.url)
        self.assertEquals(response.status_code, 400)

    def test_clear_voting_removes_attendee_vote(self):
        vote = self.talk.attendeevote_set.create(
            attendee=self.attendee, score=4)
        self.client.login(username=self.user.email, password=self.password)
        response = self.client.post(
            self.url, data={'talk-id': self.talk.id})
        self.assertEquals(response.status_code, 200)
        self.assertJSONEqual(response.content, {'message': 'vote deleted'})
        self.assertRaises(AttendeeVote.DoesNotExist, vote.refresh_from_db)

    def test_clear_voting_does_not_fail_with_no_existing_attendee_vote(self):
        self.client.login(username=self.user.email, password=self.password)
        response = self.client.post(
            self.url, data={'talk-id': self.talk.id})
        self.assertEquals(response.status_code, 200)
        self.assertJSONEqual(response.content, {'message': 'vote deleted'})
