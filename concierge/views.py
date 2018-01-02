import csv
import datetime
import pytz
import stripe

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import inlineformset_factory
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone, formats
from django.views.decorators.http import require_POST

from accounts.forms import CustomUserForm, CustomUserProfileForm
from accounts.helpers import send_welcome_email, send_subscription_receipt_email, create_customers_from_upload, send_new_customer_email, create_customer_subscription
from accounts.models import Customer, Rider
from billing.models import Plan, GroupMembership, Balance, StripeCustomer
from billing.forms import StripeCustomerForm, AdminPaymentForm, GiftForm
from billing.utils import get_stripe_subscription, get_customer_stripe_accounts
from common.utils import soon
from concierge.forms import CustomUserRegistrationForm, RiderForm, CustomerForm, DestinationForm, ActivityForm, AccountHolderForm, CustomerUploadForm
from concierge.models import Touch
from rides.forms import HomeForm
from rides.models import Destination, Ride


def dashboard(request, template='concierge/dashboard.html'):
    if not request.user.is_authenticated:
        return redirect('concierge_login')

    if not request.user.is_staff:
        messages.add_message(request, messages.WARNING, 'Sorry, you\'re not allowed to go to the Concierge portal! Here\'s your profile:')
        return redirect('profile')

    if request.method == "POST":
        customer_id = request.POST.get('customer_id', None)
        if customer_id:
            return redirect('customer_detail', customer_id)

    to_contact = Customer.objects \
                    .filter(intro_call=False) \
                    .filter(is_active=True) \
                    .exclude(plan__isnull=True) \
                    .select_related('user') \
                    .select_related('user__profile') \
                    .select_related('plan') \
                    .order_by('user__date_joined')

    to_contact = [customer for customer in to_contact if customer.ready_to_ride]

    d = {
        'to_contact': to_contact,
        'today': datetime.date.today()
    }

    return render(request, template, d)


def upcoming_rides(request, template='concierge/upcoming_rides.html'):
    if not request.user.is_authenticated:
        return redirect('concierge_login')

    if not request.user.is_staff:
        messages.add_message(request, messages.WARNING, 'Sorry, you\'re not allowed to go to the Concierge portal! Here\'s your profile:')
        return redirect('profile')

    now = timezone.now()
    week_from_now = now + datetime.timedelta(days=7)
    rides = Ride.objects.filter(start_date__gte=now) \
                        .filter(start_date__lt=week_from_now) \
                        .exclude(cancelled=True) \
                        .order_by('start_date') \
                        .select_related('destination') \
                        .select_related('start') \
                        .prefetch_related('customer') \
                        .prefetch_related('customer__user') \
                        .prefetch_related('customer__user__profile') \

    d = {
        'rides': rides,
        'upcoming_page': True,
        'active_count': Ride.active.count()
    }

    return render(request, template, d)


def active_rides(request, template='concierge/active_rides.html'):
    if not request.user.is_authenticated:
        return redirect('concierge_login')

    if not request.user.is_staff:
        messages.add_message(request, messages.WARNING, 'Sorry, you\'re not allowed to go to the Concierge portal! Here\'s your profile:')
        return redirect('profile')

    rides = Ride.active \
                .order_by('start_date') \
                .select_related('destination') \
                .select_related('start') \
                .prefetch_related('customer') \
                .prefetch_related('customer__user') \
                .prefetch_related('customer__user__profile') \

    for ride in rides:
        if ride.customer.last_ride.destination == ride.customer.home:
            ride.at_home = True
        else:
            ride.at_home = False

    d = {
        'rides': rides,
        'active_page': True,
        'active_count': rides.count()
    }

    return render(request, template, d)


def rides_history(request, template='concierge/rides_history.html'):
    if not request.user.is_authenticated:
        return redirect('concierge_login')

    if not request.user.is_staff:
        messages.add_message(request, messages.WARNING, 'Sorry, you\'re not allowed to go to the Concierge portal! Here\'s your profile:')
        return redirect('profile')

    rides = Ride.objects.filter(complete=True).order_by('-start_date').prefetch_related('customer')

    d = {
        'rides': rides,
        'history_page': True,
        'active_count': Ride.active.count()
    }
    return render(request, template, d)


@staff_member_required
def customer_list(request, template='concierge/customer_list_active.html'):
    active_customers = Customer.active.all()
    inactive_customers = Customer.inactive.all()

    d = {
        'customers': active_customers,
        'active_count': active_customers.count(),
        'inactive_count': inactive_customers.count(),
        'active_page': True
    }

    return render(request, template, d)


@staff_member_required
def customer_list_inactive(request, template='concierge/customer_list_inactive.html'):
    active_customers = Customer.active.all()
    inactive_customers = Customer.inactive.all()

    d = {
        'customers': inactive_customers,
        'active_count': active_customers.count(),
        'inactive_count': inactive_customers.count(),
        'inactive_page': True
    }

    return render(request, template, d)


@staff_member_required
def customer_create(request, template='concierge/customer_create.html'):

    errors = []
    error_count = []

    if request.method == 'GET':
        register_form = CustomUserRegistrationForm(prefix='reg')
        customer_form = CustomerForm(prefix='cust')
        home_form = HomeForm(prefix='home')
        rider_form = RiderForm(prefix='rider')
    else:
        register_form = CustomUserRegistrationForm(request.POST, prefix='reg')
        customer_form = CustomerForm(request.POST, prefix='cust')
        home_form = HomeForm(request.POST, prefix='home')
        rider_form = RiderForm(request.POST, prefix='rider')

        if all([
                register_form.is_valid(),
                customer_form.is_valid(),
                home_form.is_valid(),
                rider_form.is_valid()]):
            # save user
            new_user = register_form.save(request)
            # populate and save customer
            new_customer = customer_form.save(commit=False)
            new_customer.user = new_user
            new_customer.registered_by = request.user
            new_customer.save()

            # populate and save home address
            home_address = home_form.save(commit=False)
            home_address.name = 'Home'
            home_address.customer = new_customer
            home_address.home = True
            home_address.added_by = request.user
            home_address.save()
            # populate and save rider info
            rider_data = rider_form.cleaned_data
            if rider_data.get('first_name', None) or rider_data.get('last_name', None) or rider_data.get('mobile_phone', None):
                rider = rider_form.save(commit=False)
                rider.customer = new_customer
                rider.save()

            new_user.profile.registration_complete = True
            new_user.profile.on_behalf = True
            new_user.profile.phone = register_form.cleaned_data['phone']
            new_user.profile.relationship = register_form.cleaned_data['relationship']
            new_user.profile.save()

            # send_new_customer_email(new_user)

            return redirect('customer_detail', new_customer.id)

        else:
            errors = [register_form.errors, customer_form.errors, home_form.errors, rider_form.errors]
            error_count = sum([len(d) for d in errors])
    d = {
        'register_form': register_form,
        'customer_form': customer_form,
        'home_form': home_form,
        'rider_form': rider_form,
        'errors': errors,
        'error_count': error_count,
        'register_page': True
    }
    return render(request, template, d)


@staff_member_required
def customer_detail(request, customer_id, template='concierge/customer_detail.html'):

    subscription = None
    customer = get_object_or_404(Customer.objects.select_related('user__profile'), pk=customer_id)
    if customer.subscription_account and customer.subscription_account.stripe_id:
        subscription = get_stripe_subscription(customer)
    rides_in_progress = Ride.in_progress.filter(customer=customer)
    tz_abbrev = ''
    customer_tz = None
    if customer.home and customer.home.timezone:
        customer_tz = customer.home.timezone

    if customer_tz:
        tz = pytz.timezone(customer_tz)
        day = tz.localize(datetime.datetime.now(), is_dst=None)
        tz_abbrev = day.tzname()

    d = {
        'customer': customer,
        'subscription': subscription,
        'timezone': tz_abbrev,
        'profile_page': True,
        'riders': customer.riders.all(),
        'lovedones': customer.lovedones.all(),
        'rides_in_progress': rides_in_progress
    }

    return render(request, template, d)


@staff_member_required
def customer_update(request, customer_id, template='concierge/customer_update.html'):
    errors = []
    customer = get_object_or_404(Customer.objects.select_related('user').select_related('user__profile'), pk=customer_id)
    home = customer.home
    RiderFormSet = inlineformset_factory(Customer,
                                         Rider,
                                         form=RiderForm,
                                         can_delete=True,
                                         extra=1)

    if request.method == "POST":
        customer_form = CustomerForm(request.POST, prefix='cust', instance=customer)
        account_holder_form = AccountHolderForm(request.POST, prefix='user', instance=customer.user)
        home_form = HomeForm(request.POST, prefix='home', instance=home, customer=customer)
        rider_formset = RiderFormSet(request.POST, instance=customer)

        if all([customer_form.is_valid(),
                home_form.is_valid(),
                account_holder_form.is_valid(),
                rider_formset.is_valid()
                ]):
            customer_form.save()
            home_form.save()
            account_holder_form.save()
            rider_formset.save()

            customer.user.profile.relationship = account_holder_form.cleaned_data['relationship']
            customer.user.profile.phone = account_holder_form.cleaned_data['phone']
            customer.user.profile.source = account_holder_form.cleaned_data['source']
            customer.user.profile.source_specific = account_holder_form.cleaned_data['source_specific']
            customer.user.profile.save()

            if customer_form.cleaned_data['group_membership']:
                customer.plan = customer_form.cleaned_data['group_membership'].plan
                customer.save()

            if '_activate' in request.POST:
                customer.is_active = True
                customer.save()
                if hasattr(customer, 'subscription'):
                    customer.subscription.is_active = True
                    customer.subscription.save()
                messages.add_message(request, messages.SUCCESS, 'Customer {} activated'.format(customer))
                return redirect('customer_detail', customer.id)

            if '_deactivate' in request.POST:
                customer.is_active = False
                customer.save()
                if hasattr(customer, 'subscription'):
                    customer.subscription.is_active = False
                    customer.subscription.save()
                messages.add_message(request, messages.SUCCESS, 'Customer {} deactivated'.format(customer))
                return redirect('customer_list')

            else:
                messages.add_message(request, messages.SUCCESS, 'Customer {} successfully updated!'.format(customer))
                return redirect('customer_detail', customer.id)
        else:
            errors = [customer_form.errors, home_form.errors, account_holder_form.errors, rider_formset.errors]
            print errors

    else:
        customer_form = CustomerForm(instance=customer, prefix='cust')
        account_holder_form = AccountHolderForm(instance=customer.user,
            prefix='user',
            initial={
                'phone': customer.user.profile.phone,
                'relationship': customer.user.profile.relationship,
                'source': customer.user.profile.source,
                'source_specific': customer.user.profile.source_specific
            })
        home_form = HomeForm(instance=customer.home, prefix='home', customer=customer)
        rider_formset = RiderFormSet(instance=customer)

    d = {
        'customer': customer,
        'customer_form': customer_form,
        'account_holder_form': account_holder_form,
        'home_form': home_form,
        'rider_formset': rider_formset,
        'update_page': True,
        'errors': errors
    }

    return render(request, template, d)


@staff_member_required
def customer_destinations(request, customer_id, template='concierge/customer_destinations.html'):

    customer = get_object_or_404(Customer.objects.select_related('user').select_related('user__profile'), pk=customer_id)

    d = {
        'customer': customer,
        'destinations_page': True,
    }

    return render(request, template, d)


@staff_member_required
def customer_destination_edit(request, customer_id, destination_id, template='concierge/destination_edit.html'):

    customer = get_object_or_404(Customer, pk=customer_id)
    destination = get_object_or_404(Destination, pk=destination_id)

    if request.method == "POST":
        destination_form = DestinationForm(request.POST, instance=destination)

        if destination_form.is_valid():

            destination_form.save()

            messages.add_message(request, messages.SUCCESS, 'Customer {}\'s Destination {} successfully updated!'.format(customer, destination.name))
            return redirect('customer_destinations', customer.id)

    else:
        destination_form = DestinationForm(instance=destination)

    d = {
        'customer': customer,
        'destination': destination,
        'destination_form': destination_form
    }

    return render(request, template, d)


@staff_member_required
def customer_destination_add(request, customer_id, template='concierge/destination_add.html'):

    customer = get_object_or_404(Customer, pk=customer_id)

    if request.method == "POST":
        destination_form = DestinationForm(request.POST)

        if destination_form.is_valid():

            new_destination = destination_form.save(commit=False)
            new_destination.customer = customer
            new_destination.added_by = request.user
            new_destination.save()

            messages.add_message(request, messages.SUCCESS, 'Destination {} successfully added!'.format(new_destination.name))
            return redirect('customer_destinations', customer.id)

    else:
        destination_form = DestinationForm()

    d = {
        'customer': customer,
        'destination_form': destination_form,
        'geolocate': customer.home
    }

    return render(request, template, d)


@staff_member_required
def customer_destination_delete(request, customer_id, destination_id):
    destination = get_object_or_404(Destination, pk=destination_id)
    customer = get_object_or_404(Customer, pk=customer_id)
    deleted = destination.delete()
    if deleted:
        messages.add_message(request, messages.SUCCESS, 'Destination successfully deleted')

    return redirect('customer_destinations', customer.id)


@staff_member_required
def payment_subscription_account_edit(request, customer_id, template="concierge/payment_subscription_account_edit.html"):

    customer = get_object_or_404(Customer, pk=customer_id)
    user = customer.user
    errors = {}
    card_errors = None

    if request.method == 'POST':
        payment_form = AdminPaymentForm(request.POST, instance=customer.subscription_account)

        if payment_form.is_valid():

            # an existing customer already has a subscription account and is in Stripe
            existing_customer = customer.subscription_account and customer.subscription_account.stripe_id
            if not existing_customer:
                # create a new customer
                try:
                    # call Stripe first in case there are card validation problems
                    create_stripe_customer = stripe.Customer.create(
                        description='{} {}'.format(payment_form.cleaned_data['first_name'], payment_form.cleaned_data['last_name']),
                        email=payment_form.cleaned_data['email'],
                        source=payment_form.cleaned_data['stripe_token'],
                        metadata={
                            'customer': '{} {}'.format(customer.full_name, customer.pk)
                        }
                    )
                    if create_stripe_customer:
                        # create our stripe customer
                        new_stripe_customer = payment_form.save()

                        # if the Stripe call went through, the card was valid and we can go ahead and use the new_stripe_customer
                        if payment_form.cleaned_data['same_card_for_both'] == '1':
                            customer.subscription_account = customer.ride_account = new_stripe_customer
                        else:
                            customer.subscription_account = new_stripe_customer

                        # set customer's plan
                        customer.plan = Plan.objects.get(pk=payment_form.cleaned_data['plan'])

                        # if chosen plan has an upfront cost, create an invoice line-item
                        if customer.plan.signup_cost:
                            # signup_cost = int((customer.plan.signup_cost - customer.plan.monthly_cost) * 100)
                            signup_cost = int(customer.plan.signup_cost * 100)
                            stripe.InvoiceItem.create(
                                customer=create_stripe_customer.id,
                                amount=signup_cost,
                                currency="usd",
                                description="Initial signup fee",
                            )

                        # handle coupon code
                        coupon_code = payment_form.cleaned_data['coupon']
                        valid_coupon = False
                        if coupon_code:
                            try:
                                stripe.Coupon.retrieve(coupon_code)
                                valid_coupon = True
                            except:
                                pass
                        if not valid_coupon:
                            coupon_code = None

                        # now attach the customer to a plan (including the optional the coupon code)
                        stripe.Subscription.create(
                            customer=create_stripe_customer.id,
                            plan=customer.plan.stripe_id,
                            idempotency_key='{}{}'.format(customer.id, datetime.datetime.now().isoformat()),
                            coupon=coupon_code
                        )

                        # store the customer's stripe id in their record
                        new_stripe_customer.stripe_id = create_stripe_customer.id

                        # save everything
                        customer.is_active = True
                        customer.save()
                        new_stripe_customer.save()

                        # everything was successful, so we can send a receipt to the user
                        send_subscription_receipt_email(user)

                        messages.add_message(request, messages.SUCCESS, 'Plan selected, billing info saved')

                # catch Stripe card validation errors
                except stripe.error.CardError as ex:
                    card_errors = 'We encountered a problem processing your credit card. The error we received was "{}" Please try a different card, or contact your bank.'.format(ex.json_body['error']['message'])

                # catch any other type of error
                except Exception as ex:
                    card_errors = 'We had trouble processing your credit card. You have not been charged. Please try again, or give us a call at 1-866-626-9879.'
            else:
                if payment_form.cleaned_data['stripe_token']:
                    # this is an existing customer, get their record from Stripe
                    stripe_cust = stripe.Customer.retrieve(customer.subscription_account.stripe_id)

                    # update their description, email, source (credit card), metadata in Stripe
                    stripe_cust.description = '{} {}'.format(payment_form.cleaned_data['first_name'], payment_form.cleaned_data['last_name'])
                    stripe_cust.email = payment_form.cleaned_data['email']
                    stripe_cust.source = payment_form.cleaned_data['stripe_token']
                    stripe_cust.metadata = {'customer': '{} {}'.format(customer.full_name, customer.pk)}

                    try:
                        # now try to save the new card in Stripe
                        stripe_cust.save()
                        payment_form.save()
                        messages.add_message(request, messages.SUCCESS, 'Billing info updated')

                    # catch Stripe card validation errors
                    except stripe.error.CardError as ex:
                        card_errors = 'We encountered a problem processing your credit card. The error we received was "{}" Please try a different card, or contact your bank.'.format(ex.json_body['error']['message'])

                    # catch any other type of error
                    except Exception as ex:
                        card_errors = 'We had trouble processing your credit card. You have not been charged. Please try again, or give us a call at 1-866-626-9879.'
            # if card_errors is still None, we didn't hit any exceptions in Stripe
            if not card_errors:

                # if the customer wants to enter a different card for rides, go to that page
                if payment_form.cleaned_data['same_card_for_both'] == '0':
                    return redirect('payment_ride_account_edit', customer.id)

                else:
                    customer.ride_account = customer.subscription_account
                    customer.save()

                # otherwise take us back to their profile in concierge
                return redirect('customer_detail', customer.id)

        # form is invalid
        else:
            errors = payment_form.errors

    # GET
    else:
        # set defaults and initials
        same_card_for_both = 0
        default_plan = Plan.objects.get(name='BRONZE')

        if customer.subscription_account and customer.ride_account and customer.subscription_account == customer.ride_account:
            same_card_for_both = 1

        if customer.subscription_account:
            payment_form = AdminPaymentForm(instance=customer.subscription_account, initial={
                'plan': customer.plan.id,
                'same_card_for_both': same_card_for_both
            })

        else:
            payment_form = AdminPaymentForm(initial={
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'same_card_for_both': 1
            })

    # context
    d = {
        'customer': customer,
        'stripe_customer': customer.subscription_account,
        'payment_form': payment_form,
        'months': range(1, 13),
        'years': range(datetime.datetime.now().year, datetime.datetime.now().year + 15),
        'soon': soon(),
        'errors': errors,
        'card_errors': card_errors
    }

    return render(request, template, d)


@staff_member_required
def payment_ride_account_edit(request, customer_id, template="concierge/payment_ride_account_edit.html"):

    customer = get_object_or_404(Customer, pk=customer_id)
    errors = {}
    card_errors = None

    if request.method == 'POST':
        existing_customer = customer.ride_account and customer.ride_account.stripe_id

        if request.POST.get('add_stripe_customer') == '1':
            payment_form = StripeCustomerForm(request.POST)
            existing_customer = False

        else:
            payment_form = StripeCustomerForm(request.POST, instance=customer.ride_account)

        if payment_form.is_valid():

            if not existing_customer:

                try:
                    create_stripe_customer = stripe.Customer.create(
                        description='{} {}'.format(payment_form.cleaned_data['first_name'], payment_form.cleaned_data['last_name']),
                        email=payment_form.cleaned_data['email'],
                        source=payment_form.cleaned_data['stripe_token'],
                        metadata={
                            'customer': '{} [{}]'.format(customer.full_name, customer.pk),
                        },
                        idempotency_key='{}{}'.format(customer.id, datetime.datetime.now().isoformat())
                    )

                    if create_stripe_customer:
                        # create our stripe customer
                        stripe_customer = payment_form.save()
                        customer.ride_account = stripe_customer

                        stripe_customer.stripe_id = create_stripe_customer.id

                        # save everything
                        customer.is_active = True
                        customer.save()
                        stripe_customer.save()

                        messages.add_message(request, messages.SUCCESS, 'Credit card saved')

                        return redirect('customer_detail', customer.id)

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
                stripe_cust.metadata = {'customer': '{} [{}]'.format(customer.full_name, customer.pk)}

                try:
                    stripe_cust.save()
                    payment_form.save()
                    messages.add_message(request, messages.SUCCESS, 'Billing info updated')

                    return redirect('customer_detail', customer.id)

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
        'same_card_for_both': customer.subscription_account and customer.ride_account and customer.subscription_account == customer.ride_account,
        'payment_form': payment_form,
        'months': range(1, 13),
        'years': range(datetime.datetime.now().year, datetime.datetime.now().year + 15),
        'soon': soon(),
        'errors': errors,
        'card_errors': card_errors
    }

    return render(request, template, d)


@require_POST
@staff_member_required
def customer_deactivate(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    customer.is_active = False
    customer.save()
    messages.add_message(request, messages.SUCCESS, '{} set to inactive'.format(customer.full_name))
    return redirect(reverse('customer_list'))


@require_POST
@staff_member_required
def customer_activate(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    customer.is_active = True
    customer.save()
    messages.add_message(request, messages.SUCCESS, '{} set to active'.format(customer.full_name))
    return redirect(reverse('customer_list'))


@staff_member_required
def customer_history(request, customer_id, template="concierge/customer_history.html"):
    customer = get_object_or_404(Customer.objects.select_related('plan').select_related('user__profile'), pk=customer_id)
    rides = Ride.objects.filter(customer=customer).order_by('-start_date').select_related('destination').select_related('start').select_related('customer').select_related('customer__plan')
    touches = Touch.objects.filter(customer=customer).order_by('-date').select_related('customer')

    d = {
        'customer': customer,
        'rides': rides,
        'touches': touches,
        'history_page': True
    }
    return render(request, template, d)


@staff_member_required
def customer_activity_add(request, customer_id, template="concierge/customer_activity_add.html"):

    customer = get_object_or_404(Customer, pk=customer_id)
    touches = Touch.objects.filter(customer=customer).order_by('-date')

    errors = {}

    if request.method == 'POST':
        activity_form = ActivityForm(request.POST)
        if activity_form.is_valid():
            activity = activity_form.save()
            activity.concierge = request.user
            activity.save()
            return redirect('customer_detail', customer_id)
        else:
            errors = activity_form.errors

    else:
        activity_form = ActivityForm()

    d = {
        'customer': customer,
        'form': activity_form,
        'touches': touches,
        'errors': errors
    }
    return render(request, template, d)


@staff_member_required
def customer_add_funds(request, customer_id, template="concierge/customer_add_funds.html"):

    customer = get_object_or_404(Customer, pk=customer_id)
    customer_stripe_accounts = get_customer_stripe_accounts(customer)
    errors = {}
    card_errors = None

    if request.method == 'POST':

        payment_form = StripeCustomerForm(request.POST, unrequire=request.POST['funds_source'] != "new")
        gift_form = GiftForm(request.POST, prefix="gift")

        if all([
                payment_form.is_valid(),
                gift_form.is_valid(),
                request.POST.get('amount', False)]):

            try:
                # Add a new credit card/Stripe customer
                if request.POST['funds_source'] == "new":
                    # create new stripe customer
                    create_stripe_customer = stripe.Customer.create(
                        description='{} {}'.format(payment_form.cleaned_data['first_name'], payment_form.cleaned_data['last_name']),
                        email=payment_form.cleaned_data['email'],
                        source=payment_form.cleaned_data['stripe_token'],
                        metadata={
                            'customer': '{} {}'.format(customer.full_name, customer.pk)
                        },
                        idempotency_key='{}{}'.format(customer.id, datetime.datetime.now().isoformat())
                    )

                    if create_stripe_customer:
                        # new stripe customer created successfully
                        new_stripe_customer = payment_form.save()
                        new_stripe_customer.stripe_id = create_stripe_customer.id
                        new_stripe_customer.customer = customer
                        new_stripe_customer.save()
                        # use the newly-created stripe customer id for the charge
                        stripe_customer = new_stripe_customer

                # charge a card/Stripe customer on file
                else:
                    stripe_customer = StripeCustomer.objects.filter(stripe_id=request.POST['funds_source']).first()

                # now create the charge for the new or existing customer
                create_stripe_charge = stripe.Charge.create(
                    amount=int(request.POST['amount']) * 100,
                    currency="usd",
                    description='Add funds to customer account: {}'.format(customer.full_name),
                    receipt_email=stripe_customer.email,
                    metadata={
                        'customer': '{} {}'.format(customer.full_name, customer.pk)
                    },
                    idempotency_key='{}{}'.format(customer.id, datetime.datetime.now().isoformat()),
                    customer=stripe_customer.stripe_id
                )

                # now create the Balance object
                if create_stripe_charge:
                    charge_amount = create_stripe_charge['amount']/100

                    try:
                        customer.balance.amount += charge_amount
                        customer.balance.user_updated = request.user
                        customer.balance.stripe_customer = stripe_customer
                        customer.balance.save()

                    except Balance.DoesNotExist:
                        new_balance = Balance(amount=charge_amount, customer=customer, user_created=request.user)
                        new_balance.save()

                    success_message = '${} successfully added to {}\'s account'.format(charge_amount, customer)

                    if request.POST.get('is_gift', False):
                        new_gift = gift_form.save(commit=False)
                        new_gift.email = stripe_customer.email
                        new_gift.customer = customer
                        new_gift.amount = request.POST['amount']
                        new_gift.save()

                        success_message += ' as a gift from {} {}'.format(new_gift.first_name, new_gift.last_name)

                        gift_note = 'Received a gift of ${} from {}'.format(charge_amount, new_gift.first_name, new_gift.last_name)
                        if new_gift.relationship:
                            gift_note += ' ({})'.format(new_gift.relationship)

                        gift_touch = Touch(
                            customer=customer,
                            concierge=request.user,
                            date=timezone.now(),
                            type=Touch.GIFT,
                            notes=gift_note
                        )
                        gift_touch.full_clean()
                        gift_touch.save()

                    if not hasattr(customer, 'subscription'):
                        create_customer_subscription(customer)

                    customer.is_active = True
                    customer.save()

                    messages.add_message(
                        request,
                        messages.SUCCESS,
                        success_message
                    )
                    funds_touch = Touch(
                        customer=customer,
                        concierge=request.user,
                        date=timezone.now(),
                        type=Touch.FUNDS,
                        notes='Added ${} to account'.format(charge_amount)
                    )
                    funds_touch.full_clean()
                    funds_touch.save()

                    return redirect('customer_detail', customer.id)

            # catch Stripe card validation errors
            except stripe.error.CardError as ex:
                print 'card errors'
                print ex
                card_errors = 'We encountered a problem processing your credit card. The error we received was "{}" Please try a different card, or contact your bank.'.format(ex.json_body['error']['message'])

            # catch any other type of error
            except Exception as ex:
                print 'other errors'
                print ex
                card_errors = 'We had trouble processing your credit card. You have not been charged. Please try again, or give us a call at 1-866-626-9879.'

        else:
            print 'form errors'
            print payment_form.errors
            print gift_form.errors
            errors = payment_form.errors

    else:
        payment_form = StripeCustomerForm()
        gift_form = GiftForm(prefix="gift")


    d = {
        'customer': customer,
        'payment_form': payment_form,
        'gift_form': gift_form,
        'months': range(1, 13),
        'years': range(datetime.datetime.now().year, datetime.datetime.now().year + 15),
        'soon': soon(),
        'errors': errors,
        'card_errors': card_errors,
        'customer_stripe_accounts': customer_stripe_accounts
    }

    return render(request, template, d)


@login_required
def concierge_settings(request, template='accounts/settings.html'):
    user = request.user

    if request.method == 'GET':
        user_form = CustomUserForm(instance=user)
        profile_form = CustomUserProfileForm(instance=user.profile)

    else:
        user_form = CustomUserForm(request.POST, instance=user)
        profile_form = CustomUserProfileForm(request.POST, instance=user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            tz = pytz.timezone(user.profile.timezone)
            day = tz.localize(datetime.datetime.now(), is_dst=None)
            tz_abbrev = day.tzname()
            messages.add_message(request, messages.SUCCESS, 'Settings saved. Your timezone is set to {} ({}).'.format(user.profile.timezone, tz_abbrev))

            return redirect('concierge_settings')

    d = {
        'user': user,
        'user_form': user_form,
        'profile_form': profile_form

    }
    return render(request, template, d)


@staff_member_required
def customer_upload(request, template="concierge/customer_upload.html"):

    results = request.session.pop('results', {})
    plans = Plan.objects.filter(active=True).order_by('id')
    groups = GroupMembership.objects.filter(active=True).order_by('id')
    residence_types = Customer.RESIDENCE_TYPE_CHOICES

    if request.method == 'POST':
        form = CustomerUploadForm(request.POST, request.FILES)

        if form.is_valid():
            upload = request.FILES['file_upload']
            if upload:
                results = create_customers_from_upload(upload, request)
                request.session['results'] = results
            else:
                messages.error(request, "No file!")

            return redirect('customer_upload')

    else:
        form = CustomerUploadForm()

    d = {
        'form': form,
        'results': results,
        'plans': plans,
        'groups': groups,
        'residence_types': residence_types
    }

    return render(request, template, d)


@staff_member_required
def customer_data_export(request, template="concierge/customer_export.html"):

    if request.method == 'POST':
        customers = Customer.objects.all()
        filters = request.POST
        filename = 'All'

        if filters['status'] == 'active':
            customers = customers.filter(is_active=True).exclude(plan__isnull=True)
            filename = 'Active'
        if filters['status'] == 'inactive':
            customers = customers.filter(Q(is_active=False) | Q(plan__isnull=True))
            filename = 'Inactive'

        response = HttpResponse(content_type='text/csv')

        writer = csv.writer(response)

        if filters['type'] == 'combined':
            filename += ' Customers (combined)'
            writer.writerow([
                'Customer Email',
                'Customer First Name',
                'Customer Last Name',
                'Account Status',
                'Plan Type',
                'Date Registered',
                'Customer Home Phone',
                'Customer Mobile Phone',
                'Account Mgr First Name',
                'Account Mgr Last Name',
                'Account Mgr Email',
                'Account Mgr Phone',
                'Rider Name',
                'Rider Phone',
                'Street 1',
                'Street 2',
                'Unit',
                'City',
                'State',
                'Zip'
            ])

            for customer in customers:
                writer.writerow([
                                customer.email,
                                customer.first_name,
                                customer.last_name,
                                customer.status,
                                customer.plan,
                                formats.date_format(customer.user.date_joined, 'SHORT_DATE_FORMAT'),
                                customer.home_phone,
                                customer.mobile_phone,
                                customer.user.first_name,
                                customer.user.last_name,
                                user_email(customer),
                                customer.user.profile.phone,
                                rider_names(customer),
                                rider_phones(customer),
                                get_street1(customer),
                                get_street2(customer),
                                get_unit(customer),
                                get_city(customer),
                                get_state(customer),
                                get_zip(customer)
                                ])

        if filters['type'] == 'customer':
            filename += ' Customers'
            writer.writerow([
                'Customer First',
                'Customer Last',
                'Customer Email',
                'User Email',
                'Home Phone',
                'Mobile Phone',
                'User Phone',
                'Loved One Phones',
                'Street 1',
                'Street 2',
                'Unit',
                'City',
                'State'
            ])

            for customer in customers:
                writer.writerow([
                                customer.first_name,
                                customer.last_name,
                                customer.email,
                                user_email(customer),
                                customer.home_phone,
                                customer.mobile_phone,
                                customer.user.profile.phone,
                                rider_phones(customer),
                                get_street1(customer),
                                get_street2(customer),
                                get_unit(customer),
                                get_city(customer),
                                get_state(customer)
                                ])

        if filters['type'] == 'user':
            filename += ' Account Holders'
            writer.writerow([
                'Account Holder First',
                'Account Holder Last',
                'Account Holder Email',
                'Account Holder Phone',
                'Customer First',
                'Customer Last',
                'Customer Home Phone',
                'Customer Mobile Phone',
                'Loved One Phones',
                'Customer City',
                'Customer State'
            ])
            for customer in customers:
                writer.writerow([
                                customer.user.first_name,
                                customer.user.last_name,
                                user_email(customer),
                                customer.user.profile.phone,
                                customer.first_name,
                                customer.last_name,
                                customer.home_phone,
                                customer.mobile_phone,
                                rider_phones(customer),
                                get_city(customer),
                                get_state(customer)
                                ])

        if filters['type'] == 'rider':
            filename += ' Riders'
            writer.writerow([
                'Rider First',
                'Rider Last',
                'Rider Relationship',
                'Rider Mobile Phone',
                'Customer First',
                'Customer Last'
            ])
            for customer in customers:
                for rider in customer.riders.all():
                    writer.writerow([
                                    rider.first_name,
                                    rider.last_name,
                                    rider.relationship,
                                    rider.mobile_phone,
                                    customer.first_name,
                                    customer.last_name
                                    ])

        response['Content-Disposition'] = 'attachment; filename="{} {}.csv"'.format(filename, datetime.datetime.now().strftime("%Y-%m-%d %H-%M"))
        return response

    else:
        d = {
            'export_page': True
        }
        return render(request, template, d)


# AJAX VIEWS
def customer_search_data(request):
    customers = Customer.active.select_related('user').select_related('user__profile').all()
    customer_list = list()
    for customer in customers:

        customer_obj = {
            'name': customer.full_name,
            'home_phone': customer.home_phone,
            'mobile_phone': customer.mobile_phone,
            'id': customer.id,
            'display': '{}'.format(customer.full_name)
        }

        tokens = [
            customer.first_name,
            customer.last_name
        ]

        if customer.home_phone:
            tokens.append(customer.home_phone)
            # tokens.extend(customer.home_phone.split('-'))
            tokens.append(customer.home_phone.replace('-', ''))
            customer_obj['display'] += ' {} (H)'.format(customer.home_phone)

        if customer.mobile_phone:
            tokens.append(customer.mobile_phone)
            # tokens.extend(customer.mobile_phone.split('-'))
            tokens.append(customer.mobile_phone.replace('-', ''))
            customer_obj['display'] += ' {} (M)'.format(customer.mobile_phone)

        if customer.user.profile.on_behalf:
            tokens.append(customer.user.first_name)
            tokens.append(customer.user.last_name)
            customer_obj['display'] += ' | Account: {}'.format(customer.user.get_full_name())

            if customer.user.profile.phone:
                tokens.append(customer.user.profile.phone)
                # tokens.extend(customer.user.profile.phone.split('-'))
                tokens.append(customer.user.profile.phone.replace('-', ''))
                customer_obj['display'] += ' {}'.format(customer.user.profile.phone)

        if customer.riders:
            riders = []
            for rider in customer.riders.all():
                tokens.append(rider.first_name)
                tokens.append(rider.last_name)
                if rider.mobile_phone:
                    tokens.append(customer.mobile_phone)
                    tokens.extend(customer.home_phone.split('-'))
                    tokens.append(customer.home_phone.replace('-', ''))
                riders.append(rider.get_full_name())
            if len(riders):
                customer_obj['display'] += ' | Riders: {}'.format(', '.join(riders))

        customer_obj['tokens'] = tokens

        customer_list.append(customer_obj)

    d = {
        'customers': customer_list
    }
    return JsonResponse(d)


def rider_phones(customer):
    numbers = []
    riders = customer.riders.all()
    for rider in riders:
        numbers.append(rider.mobile_phone)

    return ' '.join(numbers)


def rider_names(customer):
    names = []
    riders = customer.riders.all()
    for rider in riders:
        names.append(rider.full_name)
    return ', '.join(names)


def user_email(customer):
    if customer.user.email and customer.user.email != customer.email:
        return customer.user.email
    return ''


def get_street1(customer):
    if customer.home and customer.home.street1:
        return customer.home.street1
    return ''


def get_street2(customer):
    if customer.home and customer.home.street2:
        return customer.home.street2
    return ''

def get_unit(customer):
    if customer.home and customer.home.unit:
        return customer.home.unit
    return ''


def get_city(customer):
    if customer.home and customer.home.city:
        return customer.home.city
    return ''


def get_state(customer):
    if customer.home and customer.home.state:
        return customer.home.state
    return ''


def get_zip(customer):
    if customer.home and customer.home.zip_code:
        return customer.home.zip_code
    return ''
