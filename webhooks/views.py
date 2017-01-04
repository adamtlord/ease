import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from billing.utils import datetime_from_timestamp
from billing.models import Invoice
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

    try:
        invoice = get_object_or_404(Invoice, stripe_id=stripe_invoice['id'])
        invoice.invoiced = stripe_invoice['attempted']
        invoice.attempt_count = stripe_invoice['attempt_count']
        invoice.total = stripe_invoice['total'] / 100
        invoice.paid = stripe_invoice['paid']

        if event_type == 'invoice.sent':
            invoice.invoiced_date = timezone.now()

        if event_type == 'invoice.payment_succeeded':
            invoice.paid_date = timezone.now()
            # apparently the invoice is sent and paid at the same time usually
            if not invoice.invoiced_date:
                invoice.invoiced_date = invoice.paid_date

        invoice.full_clean()
        invoice.save()

        if invoice.invoiced:
            new_touch = Touch(
                customer=invoice.customer,
                date=timezone.now(),
                type=Touch.BILLING,
                notes='{}: ${} [Stripe ID {}]'.format(event_type, stripe_invoice['total'] / 100, stripe_invoice['id'])
            )
            new_touch.full_clean()
            new_touch.save()

    except:
        pass

    return HttpResponse(status=200)
