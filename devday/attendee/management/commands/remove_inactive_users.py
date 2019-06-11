"""
Implement a management command to remove inactive users that exist longer than
the activation period.
"""
from datetime import timedelta

from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone

from attendee.models import DevDayUser


class Command(BaseCommand):
    help = (
        "Remove all inactive users that are older than the configured ACTIVATION_DAYS"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            default=False,
            help="Do not delete users",
        )

    def handle(self, *args, **options):
        now = timezone.now()
        cutoff_date = now - timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)

        if options["verbosity"] > 1:
            self.stdout.write(
                "delete inactive users that are older than {}".format(cutoff_date)
            )

        users = DevDayUser.objects.filter(
            is_active=False, date_joined__lte=cutoff_date
        ).order_by("email")

        if options["verbosity"] > 1:
            if options["dry_run"]:
                self.stdout.write("dry run, no actual deletions")
            self.stdout.write("will delete the following users:")
            for user in users:
                self.stdout.write(
                    "{} (joined {})".format(user.get_username(), user.date_joined)
                )
        if not options["dry_run"]:
            users.delete()
