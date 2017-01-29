from django.test import TestCase
from django.utils import timezone

from twitterfeed.admin import show_on_site, hide_on_site
from twitterfeed.models import Tweet


class TestTweetAdminActions(TestCase):
    def setUp(self):
        self.tweet1 = Tweet.objects.create(
            twitter_id='0815',
            created_at=timezone.now(), show_on_site=False)
        self.tweet2 = Tweet.objects.create(
            twitter_id='4711',
            created_at=timezone.now(), show_on_site=True)

    def test_show_on_site(self):
        show_on_site(None, None, Tweet.objects.all())
        self.tweet1.refresh_from_db()
        self.assertTrue(self.tweet1.show_on_site)

    def test_hide_on_site(self):
        hide_on_site(None, None, Tweet.objects.all())
        self.tweet2.refresh_from_db()
        self.assertFalse(self.tweet2.show_on_site)
