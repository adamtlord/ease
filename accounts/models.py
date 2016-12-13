from __future__ import unicode_literals
import pytz
import datetime
from dateutil.relativedelta import relativedelta

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from localflavor.us.models import PhoneNumberField

from common.models import Location
from billing.utils import get_stripe_subscription
from accounts.managers import CustomUserManager
from accounts.const import TEXT_UPDATE_CHOICES, TEXT_UPDATES_NEVER
from billing.models import StripeCustomer, Plan
from rides.models import Ride


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    first_name = models.CharField(verbose_name='first name', max_length=30, blank=True)
    last_name = models.CharField(verbose_name='last name', max_length=30, blank=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(
        verbose_name='staff status',
        default=False,
        help_text='Designates whether the user can log into this admin site.',
    )
    is_active = models.BooleanField(
        verbose_name='active',
        default=True,
        help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.'
    )
    date_joined = models.DateTimeField(verbose_name='date joined', default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'

    def get_full_name(self):
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def get_customer(self):
        return self.customer

    def __unicode__(self):
        return self.get_full_name()

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'


@receiver(post_save, sender=CustomUser, dispatch_uid='create_user_profile')
def create_user_profile(sender, **kwargs):
    """Automatically create UserProfile for newly created, non-raw User."""
    # If save is "raw" (coming from a fixture), don't create profile--
    # it should be manually specified in a fixture along with User object.
    if kwargs.get('created', True) and not kwargs.get('raw', False):
        UserProfile.objects.create(user=kwargs.get('instance'))


class UserProfile(models.Model):
    """Profile for User, automatically created in User.save()."""
    FRIEND_FAMILY = 'FRIEND_FAMILY'
    AD_ONLINE = 'AD_ONLINE'
    AD_PRINT = 'AD_PRINT'
    MEDIA = 'MEDIA'
    OTHER = 'OTHER'

    SOURCE_CHOICES = (
        (None, ''),
        (FRIEND_FAMILY, 'Friend or family member'),
        (AD_ONLINE, 'Online ad'),
        (AD_PRINT, 'Print ad'),
        (MEDIA, 'Media or news coverage'),
        (OTHER, 'Other'),
    )

    user = models.OneToOneField(CustomUser, related_name='profile')
    registration_complete = models.BooleanField(default=False)
    on_behalf = models.BooleanField(default=False)
    relationship = models.CharField(max_length=100, blank=True, null=True)
    receive_updates = models.BooleanField(default=False)
    source = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return "%s's profile" % self.user


class Contact(models.Model):
    """ Abstract model for storing basic contact info"""
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)
    mobile_phone = PhoneNumberField(blank=True, null=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return '{} {}'.format(self.first_name, self.last_name)


class Customer(Contact):
    """ Represents a primary user of the service """
    APARTMENT = 'AP'
    ASSISTED_LIVING = 'AL'
    RETIREMENT_COMMUNITY = 'RT'
    SINGLE_FAMILY_HOME = 'SF'
    SKILLED_NURSING = 'SN'

    RESIDENCE_TYPE_CHOICES = (
        (None, ''),
        (APARTMENT, 'Apartment'),
        (ASSISTED_LIVING, 'Assisted Living Facility'),
        (RETIREMENT_COMMUNITY, 'Retirement Community'),
        (SINGLE_FAMILY_HOME, 'Single Family Home'),
        (SKILLED_NURSING, 'Skilled Nursing Facility'),
    )

    HOME_PHONE = 'h'
    MOBILE_PHONE = 'm'

    PREFERRED_PHONE_CHOICES = (
        (HOME_PHONE, 'Home'),
        (MOBILE_PHONE, 'Mobile'),
    )

    user = models.OneToOneField(CustomUser)
    known_as = models.CharField(max_length=50, blank=True, null=True)
    dob = models.DateField(blank=True, null=True, verbose_name="Date of birth")
    last_ride = models.ForeignKey('rides.Ride', blank=True, null=True, related_name='last_ride')
    spent_to_date = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=9)
    residence_type = models.CharField(max_length=2, choices=RESIDENCE_TYPE_CHOICES, default=SINGLE_FAMILY_HOME)
    residence_instructions = models.TextField(blank=True, null=True)
    special_assistance = models.CharField(max_length=1024, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    home_phone = PhoneNumberField(blank=True, null=True)
    preferred_phone = models.CharField(max_length=2, choices=PREFERRED_PHONE_CHOICES, default=HOME_PHONE)
    send_updates = models.PositiveSmallIntegerField(choices=TEXT_UPDATE_CHOICES, default=TEXT_UPDATES_NEVER)
    subscription_account = models.ForeignKey(StripeCustomer, blank=True, null=True, related_name='subscription_customer')
    ride_account = models.ForeignKey(StripeCustomer, blank=True, null=True, related_name='ride_customer')
    plan = models.ForeignKey(Plan, blank=True, null=True)
    intro_call = models.BooleanField(default=False)

    @property
    def full_name(self):
        return '{} {}'.format(self.first_name, self.last_name)

    @property
    def age(self):
        return relativedelta(datetime.datetime.now(), self.dob).years

    @property
    def home(self):
        return self.destination_set.filter(home=True).first()

    @property
    def destinations(self):
        return self.destination_set.exclude(home=True)

    @property
    def rider(self):
        return self.riders.first()

    @property
    def rides(self):
        return self.ride_set.all().order_by('-end_date')

    def get_rides_this_month(self):
        if self.plan:
            subscription = get_stripe_subscription(self)
            start_of_billing_period = pytz.utc.localize(datetime.datetime.fromtimestamp(subscription.current_period_start))
            rides = Ride.objects.filter(customer=self).filter(end_date__gt=start_of_billing_period)
            return rides
        return []

    @property
    def rides_this_month(self):
        count = self.get_rides_this_month().count()
        if not count:
            count = 0
        return count

    @property
    def included_rides_this_month(self):
        plan = self.plan
        if plan.included_rides_per_month:
            max_distance = plan.ride_distance_limit
            neighborhood_rides = self.get_rides_this_month().filter(distance__lte=max_distance)
            if not neighborhood_rides:
                neighborhood_rides = 0
        else:
            neighborhood_rides = self.rides_this_month()
        return neighborhood_rides

    @property
    def ready_to_ride(self):
        if self.ride_account and self.subscription_account and self.plan:
            return True
        else:
            return False

    @property
    def missing(self):
        missing_items = []
        if not self.ride_account:
            missing_items.append('No rides account')
        if not self.subscription_account:
            missing_items.append('No subscription account')
        if not self.plan:
            missing_items.append('No plan selected')
        return missing_items

    @property
    def rides_ready_to_bill(self):
        return Ride.ready_to_bill.filter(customer=self)

    def __unicode__(self):
        return '{} {}'.format(self.first_name, self.last_name)


class Rider(Contact):
    """ An additional rider on an account. Must share a residence with primary customer. """
    customer = models.ForeignKey(Customer, related_name="riders")
    relationship = models.CharField(max_length=100, blank=True, null=True)
    send_updates = models.PositiveSmallIntegerField(choices=TEXT_UPDATE_CHOICES, default=TEXT_UPDATES_NEVER)

    def get_full_name(self):
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()


class LovedOne(Location, Contact):
    """ A friend or family member who may be the account holder or may wish to receive updates.
        Possibly use these as destinations, or destination choices?
    """

    customer = models.ForeignKey(Customer, related_name="lovedones")
    relationship = models.CharField(max_length=100, blank=True, null=True)
    receive_updates = models.BooleanField(default=False)

    def __unicode__(self):
        return '{} {} ({})'.format(self.first_name, self.last_name, self.relationship)
