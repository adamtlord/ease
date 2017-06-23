import json

from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from billing.utils import datetime_from_timestamp
from billing.models import Invoice, StripeCustomer
from concierge.models import Touch

# INVOICE
# {
#     'object': 'event',
#     'pending_webhooks': 1,
#     'created': 1326853478,
#     'data': {
#         'object': {
#             'amount_due': 4524
#             'application_fee': None,
#             'attempt_count': 1,
#             'attempted': False,
#             'charge': 'ch_00000000000000',
#             'closed': True,
#             'currency': 'usd',
#             'customer': 'cus_00000000000000',
#             'date': 1482367000,
#             'description': None,
#             'discount': None,
#             'ending_balance': 0,
#             'forgiven': False,
#             'id': 'in_00000000000000',
#             'livemode': False,
#             'metadata': {},
#             'next_payment_attempt': None,
#             'object': 'invoice',
#             'paid': True,
#             'period_end': 1482367000,
#             'period_start': 1481329967,
#             'receipt_number': None,
#             'starting_balance': 0,
#             'statement_descriptor': None,
#             'subscription': None,
#             'subtotal': 4524,
#             'tax': None,
#             'tax_percent': None,
#             'total': 4524,
#             'webhooks_delivered_at': 1482367001,
#             'lines': {
#                 'url': '/v1/invoices/in_19TKZYK2sMDdae4KZ2x2M7cL/lines',
#                 'total_count': 1,
#                 'object': 'list',
#                 'data': [{
#                     'discountable': True,
#                     'livemode': True,
#                     'description': None,
#                     'subscription': None,
#                     'proration': False,
#                     'object': 'line_item',
#                     'period': {
#                         'start': 1481837142,
#                         'end': 1485936000
#                     },
#                     'currency': 'usd',
#                     'amount': 0,
#                     'plan': {
#                         'interval': 'month',
#                         'name': 'Gift Certificate',
#                         'created': 1481675670,
#                         'object': 'plan',
#                         'interval_count': 1,
#                         'statement_descriptor': None,
#                         'currency': 'usd',
#                         'amount': 0,
#                         'trial_period_days': None,
#                         'livemode': False,
#                         'id': 'intro',
#                         'metadata': {}
#                     },
#                     'quantity': 1,
#                     'type': 'subscription',
#                     'id': 'sub_9kbxNp95Qf82xD',
#                     'metadata': {}
#                 }]
#             },
#         }
#     },
#     'livemode': False,
#     'request': None,
#     'type': 'invoice.created',
#     'id': 'evt_00000000000000',
#     'api_version': '2016-07-06'
# }

# CHARGE
# {
#   "created": 1326853478,
#   "livemode": false,
#   "id": "evt_00000000000000",
#   "type": "charge.failed",
#   "object": "event",
#   "request": null,
#   "pending_webhooks": 1,
#   "api_version": "2017-02-14",
#   "data": {
#     "object": {
#       "id": "ch_00000000000000",
#       "object": "charge",
#       "amount": 3000,
#       "amount_refunded": 0,
#       "application": null,
#       "application_fee": null,
#       "balance_transaction": "txn_00000000000000",
#       "captured": true,
#       "created": 1490818219,
#       "currency": "usd",
#       "customer": "cus_00000000000000",
#       "description": null,
#       "destination": null,
#       "dispute": null,
#       "failure_code": null,
#       "failure_message": null,
#       "fraud_details": {},
#       "invoice": "in_00000000000000",
#       "livemode": false,
#       "metadata": {},
#       "on_behalf_of": null,
#       "order": null,
#       "outcome": {
#         "network_status": "approved_by_network",
#         "reason": null,
#         "risk_level": "normal",
#         "seller_message": "Payment complete.",
#         "type": "authorized"
#       },
#       "paid": false,
#       "receipt_email": null,
#       "receipt_number": null,
#       "refunded": false,
#       "refunds": {
#         "object": "list",
#         "data": [],
#         "has_more": false,
#         "total_count": 0,
#         "url": "/v1/charges/ch_1A2n7XK2sMDdae4KHRuUJZ68/refunds"
#       },
#       "review": null,
#       "shipping": null,
#       "source": {
#         "id": "card_00000000000000",
#         "object": "card",
#         "address_city": null,
#         "address_country": null,
#         "address_line1": null,
#         "address_line1_check": null,
#         "address_line2": null,
#         "address_state": null,
#         "address_zip": null,
#         "address_zip_check": null,
#         "brand": "Visa",
#         "country": "US",
#         "customer": "cus_00000000000000",
#         "cvc_check": null,
#         "dynamic_last4": null,
#         "exp_month": 12,
#         "exp_year": 2017,
#         "funding": "credit",
#         "last4": "4242",
#         "metadata": {},
#         "name": null,
#         "tokenization_method": null
#       },
#       "source_transfer": null,
#       "statement_descriptor": "Arrive membership",
#       "status": "succeeded",
#       "transfer_group": null
#     }
#   }
# }
# @require_POST
# @csrf_exempt
# def invoice_item(request):

#     event = json.loads(request.body)

#     try:
#         ride = get_object_or_404(Ride, invoice_item_id=event['data']['object']['id'])
#         ride.invoice_id = event['data']['object']['invoice']
#         ride.full_clean()
#         ride.save()
#     except:
#         pass

#     return HttpResponse(status=200)

# invoice.created
# invoice.payment_succeeded
# invoice.sent
# invoice.updated


@require_POST
@csrf_exempt
def invoice(request):

    event = json.loads(request.body)
    event_type = event['type']
    stripe_invoice = event['data']['object']
    stripe_cust_id = stripe_invoice['customer']
    customer = None

    try:
        invoice = get_object_or_404(Invoice, stripe_id=stripe_invoice['id'])
        invoice.invoiced = stripe_invoice['attempted']
        invoice.attempt_count = stripe_invoice['attempt_count']
        invoice.total = stripe_invoice['total'] / 100
        invoice.paid = stripe_invoice['paid']
        invoice_type = 'Ride'

        if event_type == 'invoice.sent':
            invoice.invoiced_date = timezone.now()

        if event_type == 'invoice.payment_succeeded':
            invoice.paid_date = timezone.now()
            # apparently the invoice is sent and paid at the same time usually
            if not invoice.invoiced_date:
                invoice.invoiced_date = invoice.paid_date

        invoice.full_clean()
        invoice.save()
        customer = invoice.customer

    except:
        # okay, this isn't an invoice associated with a ride. that means it must be
        # a customer (a subscription payment), so we need to find the customer
        stripe_customer = get_object_or_404(StripeCustomer, stripe_id=stripe_cust_id)

        if stripe_customer.subscription_customer.count():
            customer = stripe_customer.subscription_customer.first()
        if stripe_customer.subscription_group_plan.count():
            customer = stripe_customer.subscription_group_plan.first()
        if stripe_customer.ride_customer.count():
            customer = stripe_customer.ride_customer.first()

        invoice_type = 'Subscription'

    new_touch = Touch(
        customer=customer,
        date=timezone.now(),
        type=Touch.BILLING,
        notes='{}: ${} ({} payment) [Stripe ID {}]'.format(event_type, stripe_invoice['total'] / 100, invoice_type, stripe_invoice['id'])
    )
    new_touch.full_clean()
    new_touch.save()

    return HttpResponse(status=200)


@require_POST
@csrf_exempt
def charge_failed(request):

    event = json.loads(request.body)
    stripe_customer = event['data']['object']['customer']

    try:
        customer = StripeCustomer.objects.filter(stripe_id=stripe_customer).ride_customer.first()

        d = {
            'customer': customer,
            'charge': event['data']['object'],
            'amount': event['data']['object']['amount'] / 100
        }

        msg_plain = render_to_string('billing/failed_charge_email.txt', d)
        msg_html = render_to_string('billing/failed_charge_email.html', d)

        to_email = settings.CUSTOMER_SERVICE_CONTACT

        send_mail(
            'Arrive: Failed Charge in Stripe',
            msg_plain,
            settings.DEFAULT_FROM_EMAIL,
            [to_email],
            html_message=msg_html,
        )

    except:
        pass
        # probably couldn't find a customer with that stripe ID, signup failed?

    return HttpResponse(status=200)
