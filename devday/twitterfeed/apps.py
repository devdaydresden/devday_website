import logging

from django.apps import AppConfig
from django.conf import settings
from django.core.management import call_command
from django.utils.translation import ugettext_lazy as _

from devday.apps import get_scheduler


def fetch_tweets():
    try:
        logger = logging.getLogger(__name__)
        logger.info("fetch tweets")
        call_command("fetch_tweets")
    except Exception as ce:
        logger = logging.getLogger(__name__)
        logger.error(ce)


def schedule_fetch_twitter_feed():
    interval = settings.TWITTERFEED_INTERVAL
    logger = logging.getLogger(__name__)
    logger.info(
        "scheduling Twitter feed fetch with a %d second interval",
        interval,
    )
    get_scheduler().add_job(
        fetch_tweets, "interval", seconds=interval, id="fetch_tweets"
    )


class TwitterFeedConfig(AppConfig):
    name = "twitterfeed"
    verbose_name = _("Twitter Feed")

    def __init__(self, app_name, app_module):
        self.job_scheduled = False
        super().__init__(app_name, app_module)

    def ready(self):
        if (not self.job_scheduled) and settings.RUN_SCHEDULED_JOBS:
            schedule_fetch_twitter_feed()
            self.job_scheduled = True
