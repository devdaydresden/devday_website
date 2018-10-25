from django.contrib.auth.models import Group, Permission
from django.test import TestCase

from talk.apps import create_talk_committee


class AppsTest(TestCase):
    def test_create_talk_committee(self):
        create_talk_committee()
        group = Group.objects.get(name=talk.COMMITTEE_GROUP)
        can_vote = Permission.objects.get(
            content_type__app_label='talk', codename='add_vote')
        can_comment = Permission.objects.get(
            content_type__app_label='talk', codename='add_talkcomment')

        self.assertIsNotNone(group)
        self.assertIsNotNone(can_vote)
        self.assertIsNotNone(can_comment)
        self.assertIn(can_vote, group.permissions.all())
        self.assertIn(can_comment, group.permissions.all())
