from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


@python_2_unicode_compatible
class TwitterSetting(models.Model):
    name = models.CharField(
        verbose_name=_("setting name"), max_length=100, unique=True, blank=False
    )
    value = models.TextField(verbose_name=_("setting value"), blank=False)

    class Meta:
        verbose_name = _("Twitter setting")
        verbose_name_plural = _("Twitter settings")

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class TwitterProfileImage(models.Model):
    user_profile_image_url = models.CharField(max_length=255, unique=True)
    image_data = models.ImageField(
        upload_to="twitter_profile",
        width_field="image_width",
        height_field="image_height",
    )
    image_width = models.SmallIntegerField(default=0)
    image_height = models.SmallIntegerField(default=0)

    class Meta:
        verbose_name = _("Twitter profile image")
        verbose_name_plural = _("Twitter profile images")

    def __str__(self):
        return self.user_profile_image_url


@python_2_unicode_compatible
class Tweet(models.Model):
    twitter_id = models.BigIntegerField(unique=True, null=False, blank=False)
    user_profile_image = models.ForeignKey(
        TwitterProfileImage, blank=True, null=True, on_delete=models.CASCADE
    )
    user_name = models.CharField(max_length=255)
    user_screen_name = models.CharField(max_length=255)
    text = models.TextField()
    plain_text = models.CharField(max_length=160)
    entities = models.TextField()
    created_at = models.DateTimeField()
    show_on_site = models.BooleanField(verbose_name=_("show on site"), default=False)

    class Meta:
        verbose_name = _("Tweet")
        verbose_name_plural = _("Tweets")

    def __str__(self):
        return "{} by {}".format(self.plain_text, self.user_screen_name)
