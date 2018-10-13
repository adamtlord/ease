import datetime
import pytz
import stripe

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from accounts.helpers import send_ride_receipt_email
from billing.models import Invoice, StripeCustomer
from concierge.models import Touch


def datetime_from_timestamp(timestamp):
    return pytz.utc.localize(datetime.datetime.fromtimestamp(timestamp))


def get_stripe_subscription(customer):
    if customer.subscription_account:
        cache_key = '{}_subscription'.format(customer.subscription_account.stripe_id)
        cached_subscription = cache.get(cache_key)
        subscription = ''

        if not cached_subscription:
            stripe_customer = stripe.Customer.retrieve(customer.subscription_account.stripe_id)

            if stripe_customer is not None:
                customer_subscriptions = stripe_customer.subscriptions
                if customer_subscriptions.data:
                    customer_subscription = customer_subscriptions.data[0]
                    cache.set(cache_key, customer_subscription, 3600)
                    subscription = customer_subscription
                else:
                    subscription = None

            else:
                subscription = None

        else:
            subscription = cached_subscription
        return subscription
    return None


def get_customer_stripe_accounts(customer):
    subscription_account = customer.subscription_account
    ride_account = customer.ride_account
    other_accounts = StripeCustomer.objects.filter(customer=customer)
    all_accounts = set(list([subscription_account] + [ride_account] + list(other_accounts)))
    return all_accounts


def invoice_customer_rides(account, customers, request):

    from accounts.helpers import send_included_rides_email

    success_included = []
    success_billed = []
    success_total = 0
    errors = []
    total = 0
    included_rides = []
    billable_rides = []

    stripe_id = account.stripe_id if account else None
    if stripe_id or [customer.balance for customer in customers]:
        for customer, rides in customers.iteritems():
            for ride in rides:
                try:
                    # the ride cost something
                    if ride.total_cost_estimate == 0:
                        # including, no fees: no billing
                        ride.total_cost = 0
                        ride.complete = True
                        ride.invoiced = True
                        included_rides.append(ride)
                        success_included.append(ride.id)
                        success_total += 1
                    else:
                        ride.total_cost = ride.total_cost_estimate
                        cost_to_bill = ride.total_cost
                        # if customer has an account
                        if hasattr(customer, 'balance'):
                            if customer.balance.amount >= ride.total_cost:
                                # customer balance can cover ride
                                ride.invoiced = True
                                ride.full_clean()
                                ride.save()
                                cost_to_bill = None
                                customer.balance.amount -= ride.total_cost
                            else:
                                # ride cost more than balance
                                if stripe_id:
                                    # charge overage to ride account
                                    cost_to_bill = ride.total_cost - customer.balance.amount
                                    customer.balance.amount = 0
                                else:
                                    # ruh roh, they're in the red.
                                    cost_to_bill = None
                                    ride.invoiced = True
                                    ride.full_clean()
                                    ride.save()
                                    customer.balance.amount -= ride.total_cost
                            customer.balance.save()
                            send_ride_receipt_email(customer, ride)
                            new_touch = Touch(
                                customer=customer,
                                date=timezone.now(),
                                type=Touch.BILLING,
                                notes='Balance debit: ${} (Ride payment)'.format(ride.total_cost)
                            )
                            new_touch.full_clean()
                            new_touch.save()
                            if customer.balance.amount < settings.BALANCE_ALERT_THRESHOLD_1 and not customer.subscription_account:
                                send_balance_alerts(customer, last_action='Ride {}, {}'.format(ride.id, ride.description))

                        if cost_to_bill:
                            invoiceitem = stripe.InvoiceItem.create(
                                customer=stripe_id,
                                amount=int(cost_to_bill * 100),
                                currency="usd",
                                description=ride.description,
                                idempotency_key='{}{}'.format(customer.id, datetime.datetime.now().isoformat())
                            )
                            ride.invoice_item_id = invoiceitem.id
                            billable_rides.append(ride)

                        success_billed.append(ride.id)
                        success_total += 1
                    ride.invoiced_by = request.user
                    ride.save()

                except Exception as ex:
                    errors.append('Ride {}: {}'.format(ride.id, ex.message))
                    continue
            total += 1

        if billable_rides:
            # step out of loop to create one invoice for whole account
            stripe_invoice = stripe.Invoice.create(customer=stripe_id)

            # get back in loop to generate invoices per-customer
            for customer in customers:
                try:
                    new_invoice = Invoice(
                        stripe_id=stripe_invoice.id,
                        customer=customer,
                        created_date=timezone.now(),
                        period_start=datetime_from_timestamp(stripe_invoice.period_start),
                        period_end=datetime_from_timestamp(stripe_invoice.period_end),
                    )

                    new_invoice.full_clean()
                    new_invoice.save()
                except Exception as ex:
                    errors.append('Customer {}: {}'.format(customer.id, ex.message))
                    continue

            for ride in billable_rides:
                try:
                    ride.invoice = new_invoice
                    ride.invoiced = True
                    ride.full_clean()
                    ride.save()
                except Exception as ex:
                    errors.append('Ride {}: {}'.format(ride.id, ex.message))

    else:
        errors.append('Customer {} has no Ride Account specified (no credit card to bill) and/or no funds in their account.'.format(customer))
        total = 1

    if included_rides:
        send_included_rides_email(customer, included_rides)

    return {
        'success_included': success_included,
        'success_billed': success_billed,
        'success_total': success_total,
        'errors': errors,
        'total': total
    }


def debit_customer_balance(customer):
    # if an inactive customer got in here somehow, skip them
    if not customer.is_active or not customer.plan:
        return False

    try:

        monthly_cost = customer.plan.monthly_cost
        available_balance = customer.balance.amount

        if available_balance >= monthly_cost:
            customer.balance.amount -= monthly_cost
            customer.balance.save()
            if customer.balance.amount < settings.BALANCE_ALERT_THRESHOLD_1 and not customer.subscription_account:
                send_balance_alerts(customer, last_action='Monthly Subscription')

        else:
            deficit = monthly_cost - available_balance
            if customer.subscription_account:
                invoiceitem = stripe.InvoiceItem.create(
                    customer=customer.subscription_account.stripe_id,
                    amount=int(deficit * 100),
                    currency="usd",
                    description="Monthly Subscription",
                    idempotency_key='{}{}'.format(customer.id, datetime.datetime.now().isoformat())
                )

                # If they have an Arrive subscription in addition to a Stripe one, we need to
                # deactivate their Arrive subscription so they don't get double-charged.
                # Monthly Billing will now be handled by Stripe.
                if customer.subscription:
                    customer.subscription.is_active = False
                    customer.subscription.save()

            else:
                # this will be negative:
                customer.balance.amount -= monthly_cost
                customer.balance.save()
                send_balance_alerts(customer, last_action='Monthly Subscription')

        return True

    except Exception as ex:
        msg_plain = 'Customer {}, Exception: {}'.format(customer, ex.message)
        send_mail(
            '[Arrive] Problem with subscription balance ',
            msg_plain,
            settings.DEFAULT_FROM_EMAIL,
            ['admin@arriverides.com']
        )
        return False


def send_balance_alerts(customer, last_action=None):

    to_email = settings.CUSTOMER_SERVICE_CONTACT

    d = {
        'customer': customer,
        'current_balance': customer.balance.amount,
        'threshhold': None,
        'last_action': last_action,
        'subscription_account': customer.subscription_account or None
    }

    if customer.balance.amount <= 0:
        msg_plain = render_to_string('billing/negative_customer_balance.txt', d)
        msg_html = render_to_string('billing/negative_customer_balance.html', d)

    else:
        if customer.balance.amount < settings.BALANCE_ALERT_THRESHOLD_2:
            d['threshold'] = settings.BALANCE_ALERT_THRESHOLD_2
            msg_plain = render_to_string('billing/customer_balance_alert.txt', d)
            msg_html = render_to_string('billing/customer_balance_alert.html', d)
        else:
            if customer.balance.amount < settings.BALANCE_ALERT_THRESHOLD_1:
                d['threshold'] = settings.BALANCE_ALERT_THRESHOLD_1
                msg_plain = render_to_string('billing/customer_balance_alert.txt', d)
                msg_html = render_to_string('billing/customer_balance_alert.html', d)

    send_mail(
        'Arrive Customer Balance Alert',
        msg_plain,
        settings.DEFAULT_FROM_EMAIL,
        to_email,
        html_message=msg_html,
    )

