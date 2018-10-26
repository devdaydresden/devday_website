from django.apps import apps, AppConfig
from django.db.models.signals import post_migrate

from talk import COMMITTEE_GROUP

class SessionsConfig(AppConfig):
    name = 'talk'

    def ready(self):
        post_migrate.connect(create_talk_committee, sender=self)


def create_talk_committee(**kwargs):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    group, created = Group.objects.get_or_create(name=COMMITTEE_GROUP)

    can_vote = Permission.objects.get(
        content_type__app_label='talk', codename='add_vote')
    can_comment = Permission.objects.get(
        content_type__app_label='talk', codename='add_talkcomment')
    group.permissions.set([can_comment, can_vote])

    group.save()
