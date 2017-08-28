from __future__ import unicode_literals

from django.apps import apps, AppConfig
from django.db.models.signals import post_migrate


class SessionsConfig(AppConfig):
    name = 'talk'

    def ready(self):
        post_migrate.connect(create_talk_committee, sender=self)


def create_talk_committee(**kwargs):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    group, created = Group.objects.get_or_create(name='talk_committee')

    can_vote = Permission.objects.get(content_type__app_label='talk', codename='add_vote')
    can_comment = Permission.objects.get(content_type__app_label='talk', codename='add_talkcomment')
    group.permissions.set([can_comment, can_vote])

    group.save()
