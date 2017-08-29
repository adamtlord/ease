import datetime
import pytz
import stripe

from django.core.cache import cache
from django.utils import timezone

from billing.models import Invoice


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


# def invoice_customer_rides(customer, rides):

#     from accounts.helpers import send_included_rides_email

#     success_included = []
#     success_billed = []
#     success_total = 0
#     errors = []
#     total = 0
#     included_rides = []
#     billable_rides = []

#     if customer.ride_account and customer.ride_account.stripe_id:
#         stripe_id = customer.ride_account.stripe_id

#     if customer.group_membership and customer.group_membership.includes_ride_cost:
#         stripe_id = customer.group_membership.ride_account.stripe_id

#     if stripe_id:

#         for ride in rides:
#             if ride.cost or ride.fees:
#                 # the ride cost something
#                 if ride.total_cost_estimate == 0:
#                     # including, no fees: no billing
#                     ride.total_cost = 0
#                     ride.complete = True
#                     ride.invoiced = True
#                     included_rides.append(ride)
#                     success_included.append(ride.id)
#                     success_total += 1
#                 else:
#                     ride.total_cost = ride.total_cost_estimate

#                     invoiceitem = stripe.InvoiceItem.create(
#                         customer=stripe_id,
#                         amount=int(ride.total_cost * 100),
#                         currency="usd",
#                         description=ride.description,
#                         idempotency_key='{}{}'.format(customer.id, datetime.datetime.now().isoformat())
#                     )
#                     ride.invoice_item_id = invoiceitem.id
#                     billable_rides.append(ride)

#                     success_billed.append(ride.id)
#                     success_total += 1

#                 ride.save()

#             else:
#                 errors.append('Ride {} has a blank cost field'.format(ride.id))

#         total += 1

#         if billable_rides:
#             stripe_invoice = stripe.Invoice.create(customer=stripe_id)

#             new_invoice = Invoice(
#                 stripe_id=stripe_invoice.id,
#                 customer=customer,
#                 created_date=timezone.now(),
#                 period_start=datetime_from_timestamp(stripe_invoice.period_start),
#                 period_end=datetime_from_timestamp(stripe_invoice.period_end),
#             )

#             new_invoice.full_clean()
#             new_invoice.save()

#             for ride in billable_rides:
#                 ride.invoice = new_invoice
#                 ride.invoiced = True
#                 ride.full_clean()
#                 ride.save()

#     else:
#         errors.append('Customer {} has no Ride Account specified (no credit card to bill)'.format(customer))
#         total = 1

#     if included_rides:
#         send_included_rides_email(customer, included_rides)

#     return {
#         'success_included': success_included,
#         'success_billed': success_billed,
#         'success_total': success_total,
#         'errors': errors,
#         'total': total
#     }

def invoice_customer_rides(account, customers, request):

    from accounts.helpers import send_included_rides_email

    success_included = []
    success_billed = []
    success_total = 0
    errors = []
    total = 0
    included_rides = []
    billable_rides = []

    stripe_id = account.stripe_id
    if stripe_id:
        for customer, rides in customers.iteritems():
            for ride in rides:
                if ride.cost or ride.fees:
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
                        invoiceitem = stripe.InvoiceItem.create(
                            customer=stripe_id,
                            amount=int(ride.total_cost * 100),
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

                else:
                    errors.append('Ride {} has a blank cost field'.format(ride.id))

            total += 1

        if billable_rides:
            # step out of loop to create one invoice for whole account
            stripe_invoice = stripe.Invoice.create(customer=stripe_id)

            # get back in loop to generate invoices per-customer
            for customer in customers:
                new_invoice = Invoice(
                    stripe_id=stripe_invoice.id,
                    customer=customer,
                    created_date=timezone.now(),
                    period_start=datetime_from_timestamp(stripe_invoice.period_start),
                    period_end=datetime_from_timestamp(stripe_invoice.period_end),
                )

                new_invoice.full_clean()
                new_invoice.save()

            for ride in billable_rides:
                ride.invoice = new_invoice
                ride.invoiced = True
                ride.full_clean()
                ride.save()

    else:
        errors.append('Customer {} has no Ride Account specified (no credit card to bill)'.format(customer))
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
