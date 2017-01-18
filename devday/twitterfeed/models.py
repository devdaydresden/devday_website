from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


@python_2_unicode_compatible
class TwitterSetting(models.Model):
    name = models.CharField(verbose_name=_("setting name"), max_length=100, unique=True, blank=False)
    value = models.TextField(verbose_name=_("setting value"), blank=False)

    class Meta:
        verbose_name = _("Twitter setting")
        verbose_name_plural = _("Twitter settings")

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Tweet(models.Model):
    twitter_id = models.BigIntegerField(unique=True, null=False, blank=False)
    user_profile_image_url = models.CharField(max_length=255, blank=True)
    user_name = models.CharField(max_length=255)
    user_screen_name = models.CharField(max_length=255)
    text = models.CharField(max_length=160)
    created_at = models.DateTimeField()
    show_on_site = models.BooleanField(default=False)

    def __str__(self):
        return "{} by {}".format(self.text, self.user_screen_name)
