from xml.etree import ElementTree

from django.contrib.auth.models import Group
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import ugettext as _

from attendee.tests import attendee_testutils
from devday.utils.devdata import DevData
from event.models import Event
from event.tests import event_testutils
from speaker.tests import speaker_testutils
from talk.forms import (TalkCommentForm,
                        EditTalkForm, TalkSpeakerCommentForm)
from talk.models import Talk, TalkFormat, TalkComment, Vote, Track, TalkMedia


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
        user.groups.add(Group.objects.get(name='talk_committee'))
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
        user.groups.add(Group.objects.get(name='talk_committee'))
        self.client.login(email=committee_email, password=password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'talk/talk_committee_details.html')

    def test_get_queryset(self):
        committee_email = 'committee@example.org'
        user, password = attendee_testutils.create_test_user(committee_email)
        user.groups.add(Group.objects.get(name='talk_committee'))
        self.client.login(email=committee_email, password=password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.talk, response.context['talk'])
        self.assertTrue(hasattr(response.context['talk'], 'average_score'))

    def test_get_context_data_unvoted(self):
        committee_email = 'committee@example.org'
        user, password = attendee_testutils.create_test_user(committee_email)
        user.groups.add(Group.objects.get(name='talk_committee'))
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
        user.groups.add(Group.objects.get(name='talk_committee'))
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
        user.groups.add(Group.objects.get(name='talk_committee'))
        self.client.login(email=committee_email, password=password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_form_invalid_sets_message(self):
        committee_email = 'committee@example.org'
        user, password = attendee_testutils.create_test_user(committee_email)
        user.groups.add(Group.objects.get(name='talk_committee'))
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
        user.groups.add(Group.objects.get(name='talk_committee'))
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
        user.groups.add(Group.objects.get(name='talk_committee'))
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
        self.user.groups.add(Group.objects.get(name='talk_committee'))
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
            Group.objects.get(name='talk_committee'))
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

        cls.url = '/{}/talk/'.format(cls.event.slug)

    def test_talk_list_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.title)

    def test_talk_list_preview_view(self):
        response = self.client.get(reverse(
            'session_list_preview',
            kwargs={'event': self.event.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.title)

    def test_infobeamer_xml_view(self):
        response = self.client.get(reverse(
            'infobeamer',
            kwargs={'event': self.event.slug}))
        self.assertEqual(response.status_code, 200)
        root = ElementTree.fromstring(response.content)
        self.assertEquals(root.tag, 'schedule')
        self.assertEquals(
            root.find('./conference/title').text,
            self.event.title)
        self.assertEquals(len(root.findall('day/room')), 4)
        self.assertEquals(len(root.findall('day/room/event')), 14)


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
