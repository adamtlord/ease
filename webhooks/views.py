import json
import pytz
import datetime

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from concierge.models import Touch
from rides.models import Ride

# INVOICE ITEM
# {
#     'object': 'event',
#     'pending_webhooks': 1,
#     'created': 1326853478,
#     'data': {
#         'object': {
#             'customer': 'cus_00000000000000',
#             'discountable': True,
#             'livemode': False,
#             'description': '12/17/2016 10:02 p.m. - 40-A Crescent Drive to 834 58th Street',
#             'subscription': None,
#             'proration': False,
#             'object': 'invoiceitem',
#             'period': {
#                 'start': 1482352482,
#                 'end': 1482352482
#             },
#             'currency': 'usd',
#             'amount': 717,
#             'plan': None,
#             'invoice': None,
#             'date': 1482352482,
#             'quantity': None,
#             'id': 'ii_00000000000000',
#             'metadata': {}
#         }
#     },
#     'livemode': False,
#     'request': None,
#     'type': 'invoiceitem.created',
#     'id': 'evt_00000000000000',
#     'api_version': '2016-07-06'
# }

# INVOICE
# {
#     'object': 'event',
#     'pending_webhooks': 1,
#     'created': 1326853478,
#     'data': {
#         'object': {
#             'application_fee': None,
#             'livemode': False,
#             'tax': None,
#             'attempt_count': 1,
#             'currency': 'usd',
#             'total': 4524,
#             'id': 'in_00000000000000',
#             'next_payment_attempt': None,
#             'receipt_number': None,
#             'statement_descriptor': None,
#             'charge': 'ch_00000000000000',
#             'closed': True,
#             'period_end': 1482367000,
#             'forgiven': False,
#             'metadata': {},
#             'description': None,
#             'webhooks_delivered_at': 1482367001,
#             'attempted': False,
#             'object': 'invoice',
#             'paid': True,
#             'discount': None,
#             'ending_balance': 0,
#             'date': 1482367000,
#             'period_start': 1481329967,
#             'subtotal': 4524,
#             'tax_percent': None,
#             'subscription': None,
#             'customer': 'cus_00000000000000',
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
#             'starting_balance': 0,
#             'amount_due': 4524
#         }
#     },
#     'livemode': False,
#     'request': None,
#     'type': 'invoice.created',
#     'id': 'evt_00000000000000',
#     'api_version': '2016-07-06'
# }


@require_POST
@csrf_exempt
def invoice_item(request):

    event = json.loads(request.body)

    try:
        ride = get_object_or_404(Ride, invoice_item_id=event['data']['object']['id'])
        ride.invoice_id = event['data']['object']['invoice']
        ride.full_clean()
        ride.save()
    except:
        pass

    return HttpResponse(status=200)


@require_POST
@csrf_exempt
def invoice(request):

    event = json.loads(request.body)
    invoice = event['data']['object']

    try:
        ride = get_object_or_404(Ride, invoice_id=invoice['id'])
        ride.invoiced = invoice['attempted']
        if ride.invoiced:
            ride.invoiced_date = pytz.utc.localize(datetime.datetime.fromtimestamp(invoice['date']))
            new_touch = Touch(
                customer=ride.customer,
                date=timezone.now(),
                type=Touch.BILLING,
                notes='Invoice sent: ${} [Stripe ID {}]'.format(invoice['total'] / 100, invoice['id'])
            )
            new_touch.full_clean()
            new_touch.save()

        ride.full_clean()
        ride.save()
    except:
        pass

    return HttpResponse(status=200)


@require_POST
@csrf_exempt
def invoice_paid(request):

    event = json.loads(request.body)
    invoice = event['data']['object']
    try:
        ride = get_object_or_404(Ride, invoice_id=invoice['id'])
        ride.paid = invoice['paid']
        if ride.paid:
            ride.paid_date = pytz.utc.localize(datetime.datetime.fromtimestamp(invoice['date']))
            new_touch = Touch(
                customer=ride.customer,
                date=timezone.now(),
                type=Touch.BILLING,
                notes='Invoice paid: ${} [Stripe ID {}]'.format(invoice['total'] / 100, invoice['id'])
            )
            new_touch.full_clean()
            new_touch.save()

        ride.full_clean()
        ride.save()
    except:
        pass

    return HttpResponse(status=200)
