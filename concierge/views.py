import datetime
import stripe

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.urlresolvers import reverse
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from accounts.helpers import send_welcome_email
from accounts.models import Customer, Rider
from billing.models import Plan
from billing.forms import StripeCustomerForm, AdminPaymentForm
from common.utils import soon
from concierge.forms import CustomUserRegistrationForm, RiderForm, CustomerForm, DestinationForm, ActivityForm
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

    to_contact = Customer.objects.filter(intro_call=False).order_by('user__date_joined')

    d = {
        'to_contact': to_contact,
        'today': datetime.date.today()
    }

    return render(request, template, d)


@staff_member_required
def customer_list(request, template='concierge/customer_list.html'):
    d = {}
    d['customers'] = Customer.objects.all()

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
            new_customer.save()
            # populate and save home address
            home_address = home_form.save(commit=False)
            home_address.name = 'Home'
            home_address.customer = new_customer
            home_address.home = True
            home_address.save()
            # populate and save rider info
            rider_data = rider_form.cleaned_data
            if rider_data.get('first_name', None) or rider_data.get('last_name', None) or rider_data.get('mobile_phone', None):
                rider = rider_form.save(commit=False)
                rider.customer = new_customer
                rider.save()

            new_user.profile.registration_complete = True
            new_user.profile.on_behalf = True
            new_user.profile.relationship = register_form.cleaned_data['relationship']
            new_user.profile.save()

            send_welcome_email(new_user)

            return redirect('customer_detail', new_customer.id)

        else:
            errors = [register_form.errors, customer_form.errors, home_form.errors, rider_form.errors]
            print errors
            error_count = sum([len(d) for d in errors])
    d = {
        'register_form': register_form,
        'customer_form': customer_form,
        'home_form': home_form,
        'rider_form': rider_form,
        'errors': errors,
        'error_count': error_count,
        }
    return render(request, template, d)


@staff_member_required
def customer_detail(request, customer_id, template='concierge/customer_detail.html'):

    customer = get_object_or_404(Customer, pk=customer_id)
    rides_in_progress = Ride.in_progress.filter(customer=customer)

    d = {
        'customer': customer,
        'profile_page': True,
        'riders': customer.riders.all(),
        'lovedones': customer.lovedones.all(),
        'rides_in_progress': rides_in_progress
    }

    return render(request, template, d)


@staff_member_required
def customer_update(request, customer_id, template='concierge/customer_update.html'):

    customer = get_object_or_404(Customer, pk=customer_id)
    home = customer.home
    RiderFormSet = inlineformset_factory(Customer,
                                         Rider,
                                         form=RiderForm,
                                         can_delete=True,
                                         extra=1)

    if request.method == "POST":
        customer_form = CustomerForm(request.POST, prefix='cust', instance=customer)
        home_form = HomeForm(request.POST, prefix='home', instance=home)
        rider_formset = RiderFormSet(request.POST, instance=customer)

        if all([customer_form.is_valid(),
                home_form.is_valid(),
                rider_formset.is_valid()
                ]):
            customer_form.save()
            home_form.save()
            rider_formset.save()

            messages.add_message(request, messages.SUCCESS, 'Customer {} successfully updated!'.format(customer))
            return redirect('customer_detail', customer.id)

    else:
        customer_form = CustomerForm(instance=customer, prefix='cust')
        home_form = HomeForm(instance=customer.home, prefix='home')
        rider_formset = RiderFormSet(instance=customer)

    d = {
        'customer': customer,
        'customer_form': customer_form,
        'home_form': home_form,
        'rider_formset': rider_formset,
        'update_page': True
    }

    return render(request, template, d)


@staff_member_required
def customer_destinations(request, customer_id, template='concierge/customer_destinations.html'):

    customer = get_object_or_404(Customer, pk=customer_id)

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
            new_destination.save()

            messages.add_message(request, messages.SUCCESS, 'Destination {} successfully added!'.format(new_destination.name))
            return redirect('customer_destinations', customer.id)

    else:
        destination_form = DestinationForm()

    d = {
        'customer': customer,
        'destination_form': destination_form
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

    if request.method == 'POST':

        payment_form = AdminPaymentForm(request.POST, instance=customer.subscription_account)

        if payment_form.is_valid():
            stripe_customer = payment_form.save()
            customer.plan = Plan.objects.get(pk=payment_form.cleaned_data['plan'])

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

            customer.save()
            stripe_customer.save()

            messages.add_message(request, messages.SUCCESS, 'Plan selected, billing info saved')

            if payment_form.cleaned_data['same_card_for_both'] == '0':
                return redirect('payment_ride_account_edit')
            return redirect('customer_detail', customer.id)

        else:
            errors = payment_form.errors

    else:
        same_card_for_both = 0
        default_plan = Plan.objects.get(name='SILVER')

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
                'same_card_for_both': 1,
                'plan': default_plan.id
            })

    d = {
        'customer': customer,
        'stripe_customer': customer.subscription_account,
        'payment_form': payment_form,
        'months': range(1, 13),
        'years': range(datetime.datetime.now().year, datetime.datetime.now().year + 15),
        'soon': soon(),
        'errors': errors,
    }

    return render(request, template, d)


@staff_member_required
def payment_ride_account_edit(request, customer_id, template="concierge/payment_ride_account_edit.html"):

    customer = get_object_or_404(Customer, pk=customer_id)
    errors = {}

    if request.method == 'POST':
        if request.POST.get('add_stripe_customer') == '1':
            payment_form = StripeCustomerForm(request.POST)
        else:
            payment_form = StripeCustomerForm(request.POST, instance=customer.ride_account)

        if payment_form.is_valid():

            stripe_customer = payment_form.save()

            customer.ride_account = stripe_customer

            if payment_form.cleaned_data['stripe_token']:
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

            customer.save()
            stripe_customer.save()

            messages.add_message(request, messages.SUCCESS, 'Credit card saved')

            return redirect('customer_detail', customer.id)

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
def customer_delete(request, customer_id):
    messages.add_message(request, messages.SUCCESS, 'Deleted')
    return redirect(reverse('customer_list'))


@staff_member_required
def customer_history(request, customer_id, template="concierge/customer_history.html"):
    customer = get_object_or_404(Customer, pk=customer_id)
    rides = Ride.objects.filter(customer=customer).order_by('-start_date')
    touches = Touch.objects.filter(customer=customer).order_by('-date')

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
            activity_form.save()
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


# AJAX VIEWS
def customer_search_data(request):
    customers = Customer.objects.all()
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
            tokens.extend(customer.home_phone.split('-'))
            tokens.append(customer.home_phone.replace('-', ''))
            customer_obj['display'] += ' {} (H)'.format(customer.home_phone)

        if customer.mobile_phone:
            tokens.append(customer.mobile_phone)
            tokens.extend(customer.home_phone.split('-'))
            tokens.append(customer.home_phone.replace('-', ''))
            customer_obj['display'] += ' {} (M)'.format(customer.mobile_phone)

        if customer.user.profile.on_behalf:
            tokens.append(customer.user.first_name)
            tokens.append(customer.user.last_name)
            customer_obj['display'] += ' | Account: {}'.format(customer.user.get_full_name())

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
