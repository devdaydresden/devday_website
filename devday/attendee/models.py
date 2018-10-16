import luhn

from base64 import urlsafe_b64encode
from hashlib import sha1
from random import SystemRandom

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.mail import send_mail
from django.db import models, IntegrityError
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _, pgettext_lazy

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
        help_text=_(('Designates whether the user can log into the admin'
                     ' site.')),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "  # \
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(
        pgettext_lazy('devday website', 'date joined'), default=timezone.now)
    twitter_handle = models.CharField(
        _('twitter handle'), blank=True, max_length=64)
    phone = models.CharField(
        verbose_name=_("Phone"), blank=True, max_length=32)
    position = models.CharField(
        _('job or study subject'), blank=True, max_length=128)
    organization = models.CharField(
        _('company or institution'), blank=True, max_length=128)
    contact_permission_date = models.DateTimeField(
        _('contact permission date'), null=True, blank=True)

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

    def get_attendee(self, event):
        """
        Return the attendee object for this user and the given event. If no
        attendee object exists, return None.
        """
        return self.attendees.filter(event=event).first()

    def get_events(self):
        """
        Return all events based on the attendee records of this user.
        """
        return Event.objects.filter(attendee__user=self)

    def __str__(self):
        full_name = self.get_full_name()
        if full_name:
            return "{} <{}>".format(full_name, self.email)
        return self.email


class AttendeeManager(models.Manager):
    def get_by_checkin_code_or_email(self, key, event):
        '''
        Returns the attendee with the given checkin code or email address. It
        is the responsibility of the caller to verify that the attendee matches
        the desired event, and that the attendee is not checked in already.
        '''
        return self.filter(
            Q(checkin_code=key) | Q(user__email=key), event=event).first()

    def is_verification_valid(self, id, verification):
        return self.get_verification(id) == verification

    def get_verification(self, id):
        m = sha1(settings.SECRET_KEY.encode())
        m.update('{:08d}'.format(int(id)).encode())
        return urlsafe_b64encode(m.digest()).decode('utf-8')


class Attendee(models.Model):
    """
    Attendee stores information related to users attending an Event. In
    addition to the user and event objects, it stores a comment field for
    how the user learned of this event, a check-in code to manually check
    the user in to the event, and the date and time the user checked in to
    the event.
    """
    event = models.ForeignKey(
        Event, verbose_name=_("Event"), null=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="attendees")

    checkin_code = models.CharField(
        _('Check-In Code'), help_text=_('Code to check in attendee manually'),
        max_length=30, null=True, unique=True)
    checked_in = models.DateTimeField(
        _('Checked-In'), help_text=_('Date and time the attendee checked in'),
        null=True, blank=True)
    source = models.TextField(
        _('source'), help_text=_('How have you become aware of this event?'),
        blank=True)

    objects = AttendeeManager()

    class Meta:
        verbose_name = _("Attendee")
        verbose_name_plural = _("Attendees")
        unique_together = [('user', 'event')]

    def save(self, *args, **kwargs):
        '''
        Ensure that the checkin code is filled in correctly.
        '''
        if not self.checkin_code:
            u = False
            while not u:
                r = str(SystemRandom().randrange(1000000, 9999999))
                self.checkin_code = luhn.append(r)
                u = Attendee.objects.filter(
                    checkin_code=self.checkin_code).count() == 0
        return super().save(*args, **kwargs)

    def get_verification(self):
        return Attendee.objects.get_verification(self.id)

    def get_checkin_url(self, event):
        return reverse(
            'attendee_checkin_url',
            kwargs={'id': self.id, 'verification': self.get_verification(),
                    'event': event})

    def check_in(self):
        if self.checked_in:
            raise IntegrityError('attendee is already checked in')
        self.checked_in = timezone.now()

    def __str__(self):
        return _('{email} at {event}').format(
            email=self.user.email, event=self.event.title)
