import pytz
from datetime import datetime
from dateutil.relativedelta import relativedelta
import csv
import string
import random
from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.utils import formats, timezone
from django.template.loader import render_to_string

from accounts.models import CustomUser, Customer
from rides.models import Destination
from billing.models import Plan, GroupMembership, Subscription

from concierge.models import Touch


def generate_password(size=12, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def convert_date(string):
    for date_format in settings.DATE_INPUT_FORMATS:
        try:
            date = datetime.strptime(string, date_format)
        except ValueError:
            pass
        else:
            break
    else:
        date = None

    return date


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


def send_subscription_receipt_email(user):
    from billing.utils import get_stripe_subscription
    customer = user.get_customer()
    account = customer.subscription_account
    plan = customer.plan
    subscription = get_stripe_subscription(customer)

    next_bill_date = formats.date_format(datetime.fromtimestamp(subscription.current_period_end), "DATE_FORMAT")

    d = {
        'account': account,
        'plan': plan,
        'next_bill_date': next_bill_date
    }

    msg_plain = render_to_string('registration/email/subscription_receipt_email.txt', d)
    msg_html = render_to_string('registration/email/subscription_receipt_email.html', d)

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


def send_ride_receipt_email(customer, ride):
    user = customer.user
    account_email = customer.ride_account.email if customer.ride_account else None
    to_name = user.first_name if user.profile.on_behalf else customer.first_name
    to_email = customer.email if customer.email else account_email if account_email else user.email

    d = {
        'ride': ride,
        'customer': customer,
        'to_name': to_name
    }

    msg_plain = render_to_string('billing/email/ride_receipt_email.txt', d)
    msg_html = render_to_string('billing/email/ride_receipt_email.html', d)

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
        notes='Sent ride receipt email (from balance)'
    )
    new_touch.full_clean()
    new_touch.save()


def send_included_rides_email(customer, rides):
    user = customer.user
    account_email = customer.ride_account.email if customer.ride_account else None
    to_name = user.first_name if user.profile.on_behalf else customer.first_name
    to_email = customer.email if customer.email else account_email if account_email else user.email

    d = {
        'rides': rides,
        'customer': customer,
        'to_name': to_name
    }

    msg_plain = render_to_string('billing/email/included_rides_email.txt', d)
    msg_html = render_to_string('billing/email/included_rides_email.html', d)

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

    msg_plain = render_to_string('accounts/email/new_customer_email.txt', d)
    msg_html = render_to_string('accounts/email/new_customer_email.html', d)

    to_email = settings.CUSTOMER_SERVICE_CONTACT

    send_mail(
        'New Arrive Signup',
        msg_plain,
        settings.DEFAULT_FROM_EMAIL,
        to_email,
        html_message=msg_html,
    )


def send_new_account_emails():

    pac = pytz.timezone(settings.TIME_ZONE)
    today = datetime.now(pac)

    todays_customers = Customer.objects.filter(user__date_joined__date=today)
    todays_customers = [customer for customer in todays_customers if customer.ready_to_ride]

    customers = len(todays_customers)
    emails_sent = 0

    if todays_customers:

        d = {
            'customers': todays_customers
        }

        msg_plain = render_to_string('accounts/email/todays_new_accounts.txt', d)
        msg_html = render_to_string('accounts/email/todays_new_accounts.html', d)

        to_email = settings.CUSTOMER_SERVICE_CONTACT

        emails_sent = send_mail(
            'New Accounts {}'.format(today.strftime('%m/%d/%Y')),
            msg_plain,
            settings.DEFAULT_FROM_EMAIL,
            to_email,
            html_message=msg_html,
        )

    return '{} customers registered today; {} emails sent'.format(customers, emails_sent)


def create_customers_from_upload(uploaded_file, request):
    UPLOAD_COLUMNS = (
        ('First'),
        ('Last'),
        ('Email'),
        ('Home Phone'),
        ('Mobile Phone'),
        ('Preferred Phone (h/m)'),
        ('DOB (M/D/YY)'),
        ('Home Address 1'),
        ('Home Address 2'),
        ('Home City'),
        ('Home State'),
        ('Home Zip'),
        ('Residence Type'),
        ('Home notes'),
        ('Plan'),
        ('Group'),
    )

    FIRST_COL = UPLOAD_COLUMNS[0]
    LAST_COL = UPLOAD_COLUMNS[1]
    EMAIL_COL = UPLOAD_COLUMNS[2]
    H_PHONE_COL = UPLOAD_COLUMNS[3]
    M_PHONE_COL = UPLOAD_COLUMNS[4]
    PREFERRED_PHONE_COL = UPLOAD_COLUMNS[5]
    DOB_COL = UPLOAD_COLUMNS[6]
    ADDRESS1_COL = UPLOAD_COLUMNS[7]
    ADDRESS2_COL = UPLOAD_COLUMNS[8]
    CITY_COL = UPLOAD_COLUMNS[9]
    STATE_COL = UPLOAD_COLUMNS[10]
    ZIP_COL = UPLOAD_COLUMNS[11]
    RESIDENCE_COL = UPLOAD_COLUMNS[12]
    HOME_NOTES_COL = UPLOAD_COLUMNS[13]
    PLAN_COL = UPLOAD_COLUMNS[14]
    GROUP_COL = UPLOAD_COLUMNS[15]

    results = {
        'errors': [],
        'success': 0,
        'created': [],
        'total': 0
    }

    reader = csv.DictReader(uploaded_file)
    for idx, row in enumerate(reader):
        results['total'] += 1
        try:
            plan = group = None
            if row[PLAN_COL]:
                plan = Plan.objects.get(pk=row[PLAN_COL])
            if row[GROUP_COL]:
                group = GroupMembership.objects.get(pk=row[GROUP_COL])

            user, created = CustomUser.objects.update_or_create(
                email=row[EMAIL_COL],
                first_name=row[FIRST_COL],
                last_name=row[LAST_COL],
                password=generate_password()
            )
            user.full_clean()
            user.save()

            customer, created = Customer.objects.update_or_create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                home_phone=row[H_PHONE_COL],
                mobile_phone=row[M_PHONE_COL],
                preferred_phone=row[PREFERRED_PHONE_COL] or 'h',
                residence_type=row[RESIDENCE_COL],
                plan=plan,
                group_membership=group,
                dob=convert_date(row[DOB_COL]),
                registered_by=request.user
            )

            customer.full_clean()
            customer.save()

            try:
                home = Destination.objects.get(
                    customer=customer,
                    home=True
                )
            except Exception as ex:
                home = Destination(
                    customer=customer,
                    home=True,
                    name='Home',
                    street1=row[ADDRESS1_COL],
                    street2=row[ADDRESS2_COL],
                    city=row[CITY_COL],
                    state=row[STATE_COL],
                    zip_code=row[ZIP_COL],
                    notes=row[HOME_NOTES_COL]
                )

            home.full_clean()
            home.save()

            results['success'] += 1
            results['created'].append('{}, {} {}'.format(user, home.city, home.state))

        except ValidationError as ex:
            for k, v in ex.message_dict.items():
                results['errors'].append(u'Row {}: {} - {}'.format(idx + 1, k, ', '.join(v)))
        except Exception as ex:
            results['errors'].append(u'Row {}: {}'.format(idx + 1, ex))

    return results


def create_customer_subscription(customer):
    # Create a customer subscription so we can track drawing down their balance monthly
    start_date = timezone.now().date()

    new_subscription = Subscription(
        customer=customer,
        is_active=True,
        next_billed_date=start_date
    )
    new_subscription.save()
