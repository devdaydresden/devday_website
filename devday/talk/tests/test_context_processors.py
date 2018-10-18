from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from attendee.models import Attendee
from attendee.tests import attendee_testutils
from event.tests import event_testutils
from speaker.tests import speaker_testutils

User = get_user_model()


class TestCommitteeMemberContextProcessor(TestCase):
    def test_is_committee_member_is_false_for_anonymous(self):
        response = self.client.get('/')
        self.assertFalse(response.context['is_committee_member'])

    def test_is_committee_member_is_false_for_attendee(self):
        user, password = attendee_testutils.create_test_user()
        event = event_testutils.create_test_event()
        Attendee.objects.create(user=user, event=event)
        self.client.login(username=user.email, password=password)
        response = self.client.get('/')
        self.assertFalse(response.context['is_committee_member'])

    def test_is_committee_member_is_false_for_speaker(self):
        speaker, user, password = speaker_testutils.create_test_speaker()
        self.client.login(username=user.email, password=password)
        response = self.client.get('/')
        self.assertFalse(response.context['is_committee_member'])

    def test_is_committee_member_is_true_for_committee_member(self):
        user, password = attendee_testutils.create_test_user()
        user.groups.add(Group.objects.get(name='talk_committee'))
        self.client.login(username=user.email, password=password)
        response = self.client.get('/')
        self.assertTrue(response.context['is_committee_member'])
