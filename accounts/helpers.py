import datetime

from django.conf import settings
from django.core.mail import send_mail
from django.utils import formats
from django.template.loader import render_to_string

from billing.utils import get_stripe_subscription


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
