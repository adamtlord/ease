import csv
import datetime
import pytz
import stripe

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import formats

from billing.forms import PaymentForm, StripeCustomerForm, CSVUploadForm, GroupMembershipFilterForm
from billing.models import GroupMembership
from billing.utils import invoice_customer_rides
from common.utils import soon
from rides.models import Ride
from rides.helpers import handle_lyft_upload, sort_rides_by_customer, sort_rides_by_ride_account


@login_required
def customer_subscription_account_edit(request, template="billing/customer_subscription_account_edit.html"):

    customer = request.user.get_customer()
    errors = {}
    card_errors = None

    if request.method == 'POST':
        payment_form = PaymentForm(request.POST, instance=customer.subscription_account)

        if payment_form.is_valid():

            # an existing customer already has a subscription account and is in Stripe
            existing_customer = customer.subscription_account and customer.subscription_account.stripe_id

            if not existing_customer:
                try:
                    create_stripe_customer = stripe.Customer.create(
                        description='{} {}'.format(payment_form.cleaned_data['first_name'], payment_form.cleaned_data['last_name']),
                        email=payment_form.cleaned_data['email'],
                        source=payment_form.cleaned_data['stripe_token'],
                        plan=customer.plan.stripe_id,
                        metadata={
                            'customer': '{} {}'.format(customer.full_name, customer.pk)
                        },
                        idempotency_key='{}{}'.format(customer.id, datetime.datetime.now().isoformat())
                    )

                    if create_stripe_customer:

                        stripe_customer = payment_form.save()

                        if payment_form.cleaned_data['same_card_for_both'] == '1':
                            customer.subscription_account = customer.ride_account = stripe_customer
                        else:
                            customer.subscription_account = stripe_customer
                            if payment_form.cleaned_data['same_card_for_both'] == '2':
                                customer.ride_account = None

                        stripe_customer.stripe_id = create_stripe_customer.id

                        customer.save()
                        stripe_customer.save()

                        messages.add_message(request, messages.SUCCESS, 'Plan selected, billing info saved')

                # catch Stripe card validation errors
                except stripe.error.CardError as ex:
                    card_errors = 'We encountered a problem processing your credit card. The error we received was "{}" Please try a different card, or contact your bank.'.format(ex.json_body['error']['message'])

                # catch any other type of error
                except Exception as ex:
                    card_errors = 'We had trouble processing your credit card. You have not been charged. Please try again, or give us a call at 1-866-626-9879.'

            else:
                if payment_form.cleaned_data['stripe_token']:
                    stripe_cust = stripe.Customer.retrieve(customer.subscription_account.stripe_id)
                    stripe_cust.description = '{} {}'.format(payment_form.cleaned_data['first_name'], payment_form.cleaned_data['last_name'])
                    stripe_cust.email = payment_form.cleaned_data['email']
                    stripe_cust.source = payment_form.cleaned_data['stripe_token']
                    stripe_cust.metadata = {'customer': '{} {}'.format(customer.full_name, customer.pk)}

                    try:
                        stripe_cust.save()
                        payment_form.save()
                        messages.add_message(request, messages.SUCCESS, 'Billing info updated')

                    # catch Stripe card validation errors
                    except stripe.error.CardError as ex:
                        card_errors = 'We encountered a problem processing your credit card. The error we received was "{}" Please try a different card, or contact your bank.'.format(ex.json_body['error']['message'])

                    # catch any other type of error
                    except Exception as ex:
                        card_errors = 'We had trouble processing your credit card. You have not been charged. Please try again, or give us a call at 1-866-626-9879.'

            if not card_errors:

                if payment_form.cleaned_data['same_card_for_both'] == '0':
                    return redirect('customer_ride_account_edit')
                else:
                    customer.ride_account = customer.subscription_account
                    customer.save()

                return redirect('profile')

        # form is invalid
        else:
            errors = payment_form.errors

    # GET
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

    # context
    d = {
        'customer': customer,
        'payment_form': payment_form,
        'months': range(1, 13),
        'years': range(datetime.datetime.now().year, datetime.datetime.now().year + 15),
        'soon': soon(),
        'errors': errors,
        'card_errors': card_errors
    }

    return render(request, template, d)


@login_required
def customer_ride_account_edit(request, group_as_customer=False, template="billing/customer_ride_account_edit.html"):

    if group_as_customer:
        try:
            customer = request.user.groupmembership
        except GroupMembership.DoesNotExist:
            pass
    else:
        customer = request.user.get_customer()

    errors = {}
    card_errors = None

    if request.method == 'POST':
        existing_customer = customer.ride_account and customer.ride_account.stripe_id
        request.POST.get('add_stripe_customer')
        if request.POST.get('add_stripe_customer') == '1':
            payment_form = StripeCustomerForm(request.POST)
            existing_customer = False

        else:
            payment_form = StripeCustomerForm(request.POST, instance=customer.ride_account)

        if payment_form.is_valid():
            if not existing_customer:
                try:
                    # create new stripe customer
                    create_stripe_customer = stripe.Customer.create(
                        description='{} {}'.format(payment_form.cleaned_data['first_name'], payment_form.cleaned_data['last_name']),
                        email=payment_form.cleaned_data['email'],
                        source=payment_form.cleaned_data['stripe_token'],
                        metadata={
                            'customer': '{} [{}]'.format(customer.name, customer.pk),
                        },
                        idempotency_key='{}{}'.format(customer.id, datetime.datetime.now().isoformat())
                    )

                    if create_stripe_customer:
                        # create our stripe customer
                        stripe_customer = payment_form.save()
                        customer.ride_account = stripe_customer

                        stripe_customer.stripe_id = create_stripe_customer.id

                        # save everything
                        customer.save()
                        stripe_customer.save()

                        messages.add_message(request, messages.SUCCESS, 'Billing info saved')

                        if group_as_customer:
                            return redirect('group_profile')
                        else:
                            return redirect('profile')

                # catch Stripe card validation errors
                except stripe.error.CardError as ex:
                    card_errors = 'We encountered a problem processing your credit card. The error we received was "{}" Please try a different card, or contact your bank.'.format(ex.json_body['error']['message'])

                # catch any other type of error
                except Exception as ex:
                    card_errors = 'We had trouble processing your credit card. You have not been charged. Please try again, or give us a call at 1-866-626-9879.'

            else:
                stripe_cust = stripe.Customer.retrieve(customer.ride_account.stripe_id)
                stripe_cust.description = '{} {}'.format(payment_form.cleaned_data['first_name'], payment_form.cleaned_data['last_name'])
                stripe_cust.email = payment_form.cleaned_data['email']
                stripe_cust.source = payment_form.cleaned_data['stripe_token']
                stripe_cust.metadata = {'customer': '{} [{}]'.format(customer.name, customer.pk)}
                try:
                    stripe_cust.save()
                    payment_form.save()
                    messages.add_message(request, messages.SUCCESS, 'Billing info updated')

                    if group_as_customer:
                        return redirect('group_profile')
                    else:
                        return redirect('profile')

                # catch Stripe card validation errors
                except stripe.error.CardError as ex:
                    card_errors = 'We encountered a problem processing your credit card. The error we received was "{}" Please try a different card, or contact your bank.'.format(ex.json_body['error']['message'])

                # catch any other type of error
                except Exception as ex:
                    card_errors = 'We had trouble processing your credit card. You have not been charged. Please try again, or give us a call at 1-866-626-9879.'

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
        'errors': errors,
        'card_errors': card_errors
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

        sorted_rides = sort_rides_by_ride_account(rides_to_bill)

        for customer, rides in sorted_rides.items():
            response = invoice_customer_rides(customer, rides, request)
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

    rides = Ride.objects.filter(Q(complete=False) | Q(cost__isnull=True)) \
                        .exclude(cancelled=True) \
                        .order_by('-start_date') \
                        .select_related('destination') \
                        .select_related('start') \
                        .prefetch_related('customer') \
                        .prefetch_related('customer__user') \
                        .prefetch_related('customer__user__profile') \
                        .prefetch_related('customer__plan') \
                        .prefetch_related('customer__group_membership') \

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

    try:
        tz = pytz.timezone(request.user.profile.timezone)
    except:
        tz = settings.TIME_ZONE

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
                'From',
                'To',
                'Date & Time',
                'Distance',
                'Cost',
                'Fees',
                'Cost to Group',
                'Company',
                'Notes'
            ])

            for customer, rides in customers.items():
                for ride in rides:
                    writer.writerow([
                                    customer,
                                    ride.id,
                                    ride.start.fullname,
                                    ride.destination.fullname,
                                    formats.date_format(ride.start_date.astimezone(tz), "SHORT_DATETIME_FORMAT"),
                                    '{} mi.'.format(ride.distance),
                                    '${0:.2f}'.format(ride.cost if ride.cost else 0),
                                    '${0:.2f}'.format(ride.total_fees_estimate),
                                    '${0:.2f}'.format(ride.cost_to_group),
                                    ride.company,
                                    unicode(ride.notes).encode("utf-8")
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

