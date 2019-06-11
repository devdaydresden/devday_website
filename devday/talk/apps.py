from django.apps import AppConfig, apps
from django.db.models.signals import post_migrate
from talk import COMMITTEE_GROUP


class SessionsConfig(AppConfig):
    name = "talk"

    def ready(self):
        post_migrate.connect(create_talk_committee, sender=self)

        # noinspection PyUnresolvedReferences
        # This import is needed for signal handling
        import talk.signals


def create_talk_committee(**kwargs):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    group, created = Group.objects.get_or_create(name=COMMITTEE_GROUP)

    can_vote = Permission.objects.get(
        content_type__app_label="talk", codename="add_vote"
    )
    can_comment = Permission.objects.get(
        content_type__app_label="talk", codename="add_talkcomment"
    )
    group.permissions.set([can_comment, can_vote])

    group.save()
