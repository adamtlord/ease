import stripe
import datetime

from django.core.cache import cache
from django.utils import timezone


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


def invoice_customer_rides(customer, rides):

    from accounts.helpers import send_included_rides_email

    success = []
    errors = []
    total = 0
    included_rides = []
    billable_rides = []

    if customer.ride_account and customer.ride_account.stripe_id:
        stripe_id = customer.ride_account.stripe_id
        for ride in rides:
            if ride.cost:
                if ride.included_in_plan:
                    ride.total_cost = 0
                    included_rides.append(ride)
                else:
                    if customer.plan.arrive_fee:
                        ride.total_cost = ride.cost + customer.plan.arrive_fee
                        ride.fee = customer.plan.arrive_fee
                    else:
                        ride.total_cost = ride.cost
                    invoiceitem = stripe.InvoiceItem.create(
                        customer=stripe_id,
                        amount=int(ride.total_cost * 100),
                        currency="usd",
                        description=ride.description
                    )
                    ride.invoice_item_id = invoiceitem.id
                    billable_rides.append(ride)

                ride.save()

                success.append('Ride {} invoiced successfully'.format(ride.id))

            else:
                errors.append('Ride {} has a blank cost field'.format(ride.id))

        total += 1

        stripe.Invoice.create(customer=stripe_id)

    else:
        errors.append('Customer {} has no Ride Account specified (no credit card to bill)'.format(customer))
        total = 1

    if included_rides:
        send_included_rides_email(customer, included_rides)

    return (success, errors, total)
