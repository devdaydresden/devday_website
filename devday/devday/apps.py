import os

from apscheduler.schedulers.background import BackgroundScheduler

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

_scheduler = None


def get_scheduler():
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone="UTC")
        _scheduler.start()
    return _scheduler


class DevDayApp(AppConfig):
    name = "devday"
    verbose_name = _("Dev Day")

    def ready(self):
        if "VAULT_URL" in os.environ:
            from .vault_integration import update_token_scheduler

            update_token_scheduler()
