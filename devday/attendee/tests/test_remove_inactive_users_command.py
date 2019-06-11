import io
from datetime import timedelta

from django.conf import settings
from django.core.management import call_command
from django.test import override_settings, TestCase
from django.utils import timezone

from attendee.models import DevDayUser


@override_settings(ACCOUNT_ACTIVATION_DAYS=2)
class TestRemoveInactiveUsersCommand(TestCase):
    def setUp(self):
        now = timezone.now()

        self.user1 = DevDayUser.objects.create(
            email="test1@example.org",
            is_active=False,
            date_joined=now - timedelta(days=(settings.ACCOUNT_ACTIVATION_DAYS + 1)),
        )
        self.user2 = DevDayUser.objects.create(
            email="test2@example.org",
            is_active=False,
            date_joined=now - timedelta(days=(settings.ACCOUNT_ACTIVATION_DAYS - 1)),
        )
        self.user3 = DevDayUser.objects.create(
            email="test3@example.org",
            is_active=True,
            date_joined=now - timedelta(days=(settings.ACCOUNT_ACTIVATION_DAYS + 1)),
        )

    def test_command_log_with_verbosity_2(self):
        buffer = io.StringIO()
        call_command("remove_inactive_users", dry_run=True, verbosity=2, stdout=buffer)
        data = buffer.getvalue()
        self.assertIn("dry run", data)
        self.assertIn("test1@example.org", data)
        self.assertNotIn("test2@example.org", data)
        self.assertNotIn("test3@example.org", data)

    def test_command_dry_run_does_not_delete(self):
        buffer = io.StringIO()
        call_command("remove_inactive_users", dry_run=True, stdout=buffer)
        self.assertEqual(len(buffer.getvalue()), 0)
        self.user1.refresh_from_db()
        self.user2.refresh_from_db()
        self.user3.refresh_from_db()
        self.assertIsNotNone(self.user1.id)
        self.assertIsNotNone(self.user2.id)
        self.assertIsNotNone(self.user3.id)

    def test_command_deletes_old_inactive_users(self):
        buffer = io.StringIO()
        call_command("remove_inactive_users", verbosity=2, stdout=buffer)
        data = buffer.getvalue()
        self.assertNotIn("dry run", data)
        self.assertIn("test1@example.org", data)
        self.assertNotIn("test2@example.org", data)
        self.assertNotIn("test3@example.org", data)
        with self.assertRaises(DevDayUser.DoesNotExist):
            self.user1.refresh_from_db()
        self.user2.refresh_from_db()
        self.user3.refresh_from_db()
        self.assertIsNotNone(self.user2.id)
        self.assertIsNotNone(self.user3.id)
