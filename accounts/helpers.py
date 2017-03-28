import datetime

from django.conf import settings
from django.core.mail import send_mail
from django.utils import formats, timezone
from django.template.loader import render_to_string

from billing.utils import get_stripe_subscription
from concierge.models import Touch


def send_welcome_email(user):

    msg_plain = render_to_string('registration/welcome_email.txt', {'user': user})
    msg_html = render_to_string('registration/welcome_email.html', {'user': user})

    send_mail(
        'Welcome to Arrive Rides!',
        msg_plain,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=msg_html,
    )

    new_touch = Touch(
        customer=user.get_customer(),
        date=timezone.now(),
        type=Touch.EMAIL,
        notes='Sent welcome email after registration'
    )
    new_touch.full_clean()
    new_touch.save()


def send_receipt_email(user):

    customer = user.get_customer()
    account = customer.subscription_account
    plan = customer.plan
    subscription = get_stripe_subscription(customer)

    next_bill_date = formats.date_format(datetime.datetime.fromtimestamp(subscription.current_period_end), "DATE_FORMAT")

    d = {
        'account': account,
        'plan': plan,
        'next_bill_date': next_bill_date
    }

    msg_plain = render_to_string('registration/receipt_email.txt', d)
    msg_html = render_to_string('registration/receipt_email.html', d)

    to_email = account.email if account.email else user.email

    send_mail(
        'Arrive Membership Confirmation',
        msg_plain,
        settings.DEFAULT_FROM_EMAIL,
        [to_email],
        html_message=msg_html,
    )

    new_touch = Touch(
        customer=user.get_customer(),
        date=timezone.now(),
        type=Touch.EMAIL,
        notes='Sent receipt email after payment'
    )
    new_touch.full_clean()
    new_touch.save()


def send_included_rides_email(customer, rides):

    user = customer.user
    account = customer.ride_account

    to_email = customer.email if customer.email else account.email if account.email else user.email

    d = {
        'rides': rides,
        'customer': customer
    }

    msg_plain = render_to_string('registration/included_rides_email.txt', d)
    msg_html = render_to_string('registration/included_rides_email.html', d)

    send_mail(
        'Thanks for riding with Arrive!',
        msg_plain,
        settings.DEFAULT_FROM_EMAIL,
        [to_email],
        html_message=msg_html,
    )

    new_touch = Touch(
        customer=customer,
        date=timezone.now(),
        type=Touch.EMAIL,
        notes='Sent included ride email'
    )
    new_touch.full_clean()
    new_touch.save()


def send_new_customer_email(user):

    customer = user.get_customer()
    profile = user.profile

    d = {
        'user': user,
        'customer': customer,
        'profile': profile
    }

    msg_plain = render_to_string('registration/new_customer_email.txt', d)
    msg_html = render_to_string('registration/new_customer_email.html', d)

    to_email = settings.CUSTOMER_SERVICE_CONTACT

    send_mail(
        'New Arrive Signup',
        msg_plain,
        settings.DEFAULT_FROM_EMAIL,
        [to_email],
        html_message=msg_html,
    )
