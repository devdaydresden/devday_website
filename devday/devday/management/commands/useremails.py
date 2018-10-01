from django.core.management import BaseCommand

from attendee.models import DevDayUser


class Command(BaseCommand):
    help = ('Print out a list of all users that have agreed to be contacted by'
            ' the team')

    def handle(self, *args, **options):
        users = DevDayUser.objects.all().filter(
            contact_permission_date__isnull=False).order_by('email')
        for user in users:
            self.stdout.write(user.email)
