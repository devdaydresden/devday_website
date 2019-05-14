import json

from django.test import TestCase
from django.urls import reverse

from devday.utils.devdata import DevData


class TwitterwallView(TestCase):
    def test_twitterwall(self):
        self.maxDiff = None
        devdata = DevData()
        devdata.create_twitter_profiles()
        devdata.create_tweets(5)
        response = self.client.get(reverse('twitterwall'))
        self.assertEqual(response.status_code, 200)
        twitterwall = json.loads(response.content.decode("utf8"))
        self.assertIn("tweets", twitterwall)
        self.assertEqual(len(twitterwall["tweets"]), 5,
            "there should be five tweets")
        self.assertTrue(
            twitterwall["tweets"][0]["time"] >
            twitterwall["tweets"][1]["time"],
            "newest tweet first")
