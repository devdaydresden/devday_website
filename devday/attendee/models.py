from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from event.models import Event


class DevDayUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        email = self.normalize_email(email)
        if not email:
            raise ValueError('The given email must be set')
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


@python_2_unicode_compatible
class DevDayUser(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    email = models.EmailField(_('email address'), unique=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into the admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "  # \
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    twitter_handle = models.CharField(_('twitter handle'), blank=True, max_length=64)
    phone = models.CharField(verbose_name=_("Phone"), blank=True, max_length=32)
    position = models.CharField(_('job or study subject'), blank=True, max_length=128)
    organization = models.CharField(_('company or institution'), blank=True, max_length=128)
    contact_permission_date = models.DateTimeField(null=True)

    objects = DevDayUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        abstract = False

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def __str__(self):
        full_name = self.get_full_name()
        if full_name:
            return "{} <{}>".format(full_name, self.email)
        return self.email


@python_2_unicode_compatible
class Attendee(models.Model):
    """
    This is a model class for an attendee.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="attendees")
    source = models.TextField(_('source'), help_text=_('How have you become aware of this event?'), blank=True)
    event = models.ForeignKey(Event, verbose_name=_("Event"))

    class Meta:
        verbose_name = _("Attendee")
        verbose_name_plural = _("Attendees")
        unique_together = [('user', 'event')]

    def __str__(self):
        return "{} / {}".format(self.user.get_full_name(), self.event)
