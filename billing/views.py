import csv
import datetime
import pytz
import stripe

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.utils import formats

from billing.forms import PaymentForm, StripeCustomerForm, CSVUploadForm, GroupMembershipFilterForm
from billing.models import GroupMembership
from billing.utils import invoice_customer_rides
from common.utils import soon
from rides.models import Ride
from rides.helpers import handle_lyft_upload, sort_rides_by_customer


@login_required
def customer_subscription_account_edit(request, template="billing/customer_subscription_account_edit.html"):

    customer = request.user.get_customer()
    errors = {}

    if request.method == 'POST':
        payment_form = PaymentForm(request.POST, instance=customer.subscription_account)
        if payment_form.is_valid():

            existing_customer = customer.subscription_account and customer.subscription_account.stripe_id

            stripe_customer = payment_form.save()

            if not existing_customer:
                if payment_form.cleaned_data['same_card_for_both'] == '1':
                    customer.subscription_account = customer.ride_account = stripe_customer
                else:
                    customer.subscription_account = stripe_customer
                    if payment_form.cleaned_data['same_card_for_both'] == '2':
                        customer.ride_account = None

                if payment_form.cleaned_data['stripe_token']:
                    create_stripe_customer = stripe.Customer.create(
                        description='{} {}'.format(stripe_customer.first_name, stripe_customer.last_name),
                        email=stripe_customer.email,
                        source=payment_form.cleaned_data['stripe_token'],
                        plan=customer.plan.stripe_id,
                        metadata={
                            'customer': '{} {}'.format(customer.full_name, customer.pk)
                        },
                        idempotency_key='{}{}'.format(customer.id, datetime.datetime.now().isoformat())
                    )

                    stripe_customer.stripe_id = create_stripe_customer.id
                    messages.add_message(request, messages.SUCCESS, 'Plan selected, billing info saved')

            else:
                if payment_form.cleaned_data['stripe_token']:
                    stripe_cust = stripe.Customer.retrieve(customer.subscription_account.stripe_id)
                    stripe_cust.description = '{} {}'.format(stripe_customer.first_name, stripe_customer.last_name)
                    stripe_cust.email = stripe_customer.email
                    stripe_cust.source = payment_form.cleaned_data['stripe_token']
                    stripe_cust.metadata = {'customer': '{} {}'.format(customer.full_name, customer.pk)}
                    stripe_cust.save()
                    messages.add_message(request, messages.SUCCESS, 'Billing info updated')

            customer.save()
            stripe_customer.save()

            if payment_form.cleaned_data['same_card_for_both'] == '0':
                return redirect('customer_ride_account_edit')
            return redirect('profile')

        else:
            errors = payment_form.errors

    else:
        same_card_for_both = 0

        if customer.subscription_account and customer.ride_account and customer.subscription_account == customer.ride_account:
            same_card_for_both = 1

        payment_form = PaymentForm(
            instance=customer.subscription_account,
            initial={
                'same_card_for_both': same_card_for_both,
                'plan': customer.plan.id
            })

    d = {
        'customer': customer,
        'payment_form': payment_form,
        'months': range(1, 13),
        'years': range(datetime.datetime.now().year, datetime.datetime.now().year + 15),
        'soon': soon(),
        'errors': errors,
    }

    return render(request, template, d)


@login_required
def customer_ride_account_edit(request, template="billing/customer_ride_account_edit.html"):
    customer = request.user.get_customer()
    errors = {}
    existing_customer = customer.ride_account and customer.ride_account.stripe_id

    if request.method == 'POST':
        if request.POST.get('add_stripe_customer') == '1':
            payment_form = StripeCustomerForm(request.POST)
            existing_customer = False
        else:
            payment_form = StripeCustomerForm(request.POST, instance=customer.ride_account)

        if payment_form.is_valid():

            stripe_customer = payment_form.save()

            customer.ride_account = stripe_customer

            if payment_form.cleaned_data['stripe_token']:
                if not existing_customer:
                    create_stripe_customer = stripe.Customer.create(
                        description='{} {}'.format(stripe_customer.first_name, stripe_customer.last_name),
                        email=stripe_customer.email,
                        source=payment_form.cleaned_data['stripe_token'],
                        metadata={
                            'customer': '{} [{}]'.format(customer.full_name, customer.pk),
                        },
                        idempotency_key='{}{}'.format(customer.id, datetime.datetime.now().isoformat())
                    )

                    stripe_customer.stripe_id = create_stripe_customer.id
                    messages.add_message(request, messages.SUCCESS, 'Billing info saved')

                else:
                    stripe_cust = stripe.Customer.retrieve(customer.ride_account.stripe_id)
                    stripe_cust.description = '{} {}'.format(stripe_customer.first_name, stripe_customer.last_name)
                    stripe_cust.email = stripe_customer.email
                    stripe_cust.source = payment_form.cleaned_data['stripe_token']
                    stripe_cust.metadata = {'customer': '{} [{}]'.format(customer.full_name, customer.pk)}
                    stripe_cust.save()
                    messages.add_message(request, messages.SUCCESS, 'Billing info updated')

            customer.save()
            stripe_customer.save()

            return redirect('profile')

        else:
            errors = payment_form.errors

    else:
        if customer.subscription_account == customer.ride_account:
            payment_form = StripeCustomerForm()
        else:
            payment_form = StripeCustomerForm(instance=customer.ride_account)

    d = {
        'customer': customer,
        'same_card_for_both': customer.subscription_account == customer.ride_account,
        'payment_form': payment_form,
        'months': range(1, 13),
        'years': range(datetime.datetime.now().year, datetime.datetime.now().year + 15),
        'soon': soon(),
        'errors': errors
    }

    return render(request, template, d)


@staff_member_required
def rides_ready_to_bill(request, template="billing/ready_to_bill.html"):

    rides = Ride.ready_to_bill.all().order_by('-start_date')
    customers = sort_rides_by_customer(rides)

    success_included = []
    success_billed = []
    success_total = 0
    errors = []
    total = 0

    if request.method == 'POST':

        idlist = request.POST.getlist('ride')
        rides_to_bill = Ride.objects.filter(id__in=idlist)
        sorted_rides = sort_rides_by_customer(rides_to_bill)

        for customer, rides in sorted_rides.items():
            response = invoice_customer_rides(customer, rides)
            success_included += response['success_included']
            success_billed += response['success_billed']
            success_total += response['success_total']
            errors += response['errors']
            total += response['total']

        rides = Ride.ready_to_bill.all()
        customers = sort_rides_by_customer(rides)

    d = {
        'ready_page': True,
        'customers': customers,
        'success_included': success_included,
        'success_billed': success_billed,
        'success_total': success_total,
        'errors': errors,
        'total': total
    }

    return render(request, template, d)


@staff_member_required
def rides_incomplete(request, template="billing/incomplete.html"):

    rides = Ride.objects.filter(Q(complete=False) | Q(cost__isnull=True)).order_by('-start_date')
    customers = sort_rides_by_customer(rides)

    d = {
        'incomplete_page': True,
        'customers': customers
    }
    return render(request, template, d)


@staff_member_required
def rides_invoiced(request, template="billing/invoiced.html"):
    rides = Ride.objects.filter(invoice__isnull=False).order_by('-start_date')

    d = {
        'invoiced_page': True,
        'rides': rides
    }
    return render(request, template, d)


@staff_member_required
def rides_upload(request, template="billing/upload.html"):

    results = {}

    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)

        if form.is_valid():
            upload = request.FILES['file_upload']
            if upload:
                results = handle_lyft_upload(request.FILES['file_upload'])
            else:
                messages.error(request, "No file!")

    else:
        form = CSVUploadForm()

    d = {
        'upload_page': True,
        'form': form,
        'results': results,
    }
    return render(request, template, d)


def group_billing(request, template="billing/group_billing.html"):
    INVOICED = 'Invoiced'
    NOT_INVOICED = 'Not Invoiced'
    EXPORT = 'export'
    UPDATE = 'update'

    search_form = GroupMembershipFilterForm(request.GET)
    customers = None
    group = None
    target_status = INVOICED

    if request.POST:
        action = request.POST.get('action')
        idlist = request.POST.getlist('ride')
        rides_to_bill = Ride.objects.filter(id__in=idlist)

        if action == EXPORT:
            customers = sort_rides_by_customer(rides_to_bill)

            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="group_membership_export.csv"'

            writer = csv.writer(response)
            writer.writerow([
                'Customer',
                'Ride ID',
                'Date & Time',
                'Distance',
                'Fee',
                'Company',
                'Notes'
            ])

            for customer, rides in customers.items():
                for ride in rides:
                    writer.writerow([
                                    customer,
                                    ride.id,
                                    formats.date_format(ride.start_date, "SHORT_DATETIME_FORMAT"),
                                    '{} mi.'.format(ride.distance),
                                    '${0:.2f}'.format(ride.customer.plan.arrive_fee),
                                    ride.company,
                                    ride.notes
                                    ])

            return response

        elif action == UPDATE:
            target_status = request.POST.get('target_status', NOT_INVOICED)
            if target_status == INVOICED:
                rides_to_bill.update(invoiced=True)
            elif target_status == NOT_INVOICED:
                rides_to_bill.update(invoiced=False)

    if request.GET:
        search_form = GroupMembershipFilterForm(request.GET)
        try:
            tz = pytz.timezone(request.user.profile.timezone)
        except:
            tz = settings.TIME_ZONE

        filters = {}
        group = None

        if search_form.is_valid():
            cd = search_form.cleaned_data
            if cd['group']:
                group = GroupMembership.objects.get(pk=request.GET.get('group', None))
                filters['customer__group_membership'] = group

                if cd['start_date']:
                    start_datetime = tz.localize(datetime.datetime.combine(cd['start_date'], datetime.datetime.min.time()), is_dst=None)
                    filters['start_date__gte'] = start_datetime

                if cd['end_date']:
                    end_datetime = tz.localize(datetime.datetime.combine(cd['end_date'], datetime.datetime.max.time()), is_dst=None)
                    filters['start_date__lt'] = end_datetime

                if cd['invoiced']:
                    filters['invoiced'] = cd['invoiced']
                    if cd['invoiced'] == 'True':
                        target_status = NOT_INVOICED

                rides = Ride.objects.filter(**filters)

                customers = sort_rides_by_customer(rides)

    d = {
        'group_page': True,
        'group': group,
        'search_form': search_form,
        'customers': customers,
        'target_status': target_status
    }

    return render(request, template, d)


def retrieve_coupon(request):
    coupon_code = request.GET.get('coupon_code', None)
    success = False
    stripe_coupon = None
    if coupon_code:
        try:
            stripe_coupon = stripe.Coupon.retrieve(coupon_code)
            message = "Found coupon code"
            success = True
        except stripe.error.InvalidRequestError:
            message = "Sorry, that coupon code is not valid."
    else:
        message = "No coupon code entered"

    d = {
        'success': success,
        'message': message,
        'stripe_coupon': stripe_coupon
    }

    return JsonResponse(d)
