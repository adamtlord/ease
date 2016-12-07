import datetime
import stripe

from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from common.decorators import anonymous_required
from accounts.forms import (CustomUserRegistrationForm, CustomerForm, RiderForm,
                            CustomerPreferencesForm, LovedOneForm, LovedOnePreferencesForm)
from billing.models import Plan
from billing.forms import PaymentForm, StripeCustomerForm
from common.utils import soon
from rides.models import Destination
from rides.forms import DestinationForm, HomeForm

stripe.api_key = settings.STRIPE_SECRET_KEY


@anonymous_required
def register_self(request, template='accounts/register.html'):
    if not settings.REGISTRATION_OPEN:
        messages.info(request, "Registration is temporarily closed. We are sorry for the inconvenience.")
        return redirect('homepage')

    if request.method == 'GET':

        plan_selection = request.GET.get('plan', None)
        if plan_selection:
            request.session['plan'] = plan_selection

        register_form = CustomUserRegistrationForm(prefix='reg')
        customer_form = CustomerForm(prefix='cust', is_self=True)
        home_form = HomeForm(prefix='home')
        rider_form = RiderForm(prefix='rider')
    else:
        register_form = CustomUserRegistrationForm(request.POST, prefix='reg')
        customer_form = CustomerForm(request.POST, prefix='cust', is_self=True)
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
            new_customer.first_name = new_user.first_name
            new_customer.last_name = new_user.last_name
            new_customer.email = new_user.email
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
            new_user.profile.save()

            authenticated_user = auth.authenticate(username=new_user.get_username(), password=register_form.cleaned_data['password1'])
            authenticated_user.backend = settings.AUTHENTICATION_BACKENDS[0]
            auth.login(request, authenticated_user)

            # Skip preferences for now because Lyft doesn't offer that
            # 2016-11-23
            return redirect('register_self_payment')
        else:
            errors = [register_form.errors, customer_form.errors, home_form.errors, rider_form.errors]
            print errors

    d = {
        'self': True,
        'lovedone': False,
        'register_form': register_form,
        'customer_form': customer_form,
        'home_form': home_form,
        'rider_form': rider_form
        }
    return render(request, template, d)


@login_required
def register_self_payment(request, template='accounts/register_payment.html'):

    if request.user.is_staff:
        redirect('dashboard')

    customer = request.user.get_customer()
    errors = {}
    selected_plan = default_plan = None

    if request.method == 'POST':
        payment_form = PaymentForm(request.POST)
        if payment_form.is_valid():

            new_stripe_customer = payment_form.save()

            customer.subscription_account = customer.ride_account = new_stripe_customer
            customer.plan = Plan.objects.get(pk=payment_form.cleaned_data['plan'])

            selected_plan = customer.plan

            create_stripe_customer = stripe.Customer.create(
                description='{} {}'.format(new_stripe_customer.first_name, new_stripe_customer.last_name),
                email=new_stripe_customer.email,
                source=payment_form.cleaned_data['stripe_token'],
                plan=customer.plan.stripe_id,
                metadata={
                    'customer': '{} {}'.format(customer.full_name, customer.pk)
                }
            )

            if customer.plan.signup_cost:
                stripe.Charge.create(
                    amount=customer.plan.signup_cost * 100,
                    currency="usd",
                    customer=create_stripe_customer.id
                )

            new_stripe_customer.stripe_id = create_stripe_customer.id

            customer.save()
            new_stripe_customer.save()

            messages.add_message(request, messages.SUCCESS, 'Congratulations! Plan selected, billing info securely saved.')

            return redirect('register_self_destinations')
        else:
            errors = payment_form.errors

    else:
        plan_selection = request.session.get('plan', None)
        if plan_selection:
            selected_plan = Plan.objects.get(name=plan_selection.upper())
            default_plan = selected_plan
        else:
            default_plan = Plan.objects.get(name="SILVER")

        payment_form = PaymentForm(initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'same_card_for_both': 1,
            'plan': selected_plan
        })

    d = {
        'self': True,
        'lovedone': False,
        'customer': customer,
        'payment_form': payment_form,
        'plan_options': Plan.objects.filter(active=True).exclude(pk=Plan.UL_GIFT),
        'months': range(1, 13),
        'years': range(datetime.datetime.now().year, datetime.datetime.now().year + 15),
        'stripe_customer': customer.subscription_account,
        'soon': soon(),
        'errors': errors,
        'default_plan': default_plan,
        'selected_plan': selected_plan,
        'errors': errors
    }

    return render(request, template, d)


@login_required
def register_self_preferences(request, template='accounts/register_preferences.html'):

    if request.user.is_staff:
        redirect('dashboard')

    customer = request.user.get_customer()

    if request.method == 'POST':
        preferences_form = CustomerPreferencesForm(request.POST, instance=customer)
        lovedone_form = LovedOneForm(request.POST)

        if preferences_form.is_valid() and lovedone_form.is_valid():
            preferences_form.save()
            lovedone = lovedone_form.save(commit=False)
            lovedone.customer = customer
            lovedone.save()

            return redirect('register_self_destinations')
    else:
        preferences_form = CustomerPreferencesForm(instance=customer)
        lovedone_form = LovedOneForm()

    d = {
        'self': True,
        'lovedone': False,
        'preferences_form': preferences_form,
        'lovedone_form': lovedone_form
    }
    return render(request, template, d)


@login_required
def register_self_destinations(request, template='accounts/register_destinations.html'):

    if request.user.is_staff:
        redirect('dashboard')

    customer = request.user.get_customer()
    home = customer.destination_set.filter(home=True).first()

    if request.method == "POST":
        destination_form = DestinationForm(request.POST)

        if destination_form.is_valid():

            new_destination = destination_form.save(commit=False)
            new_destination.customer = customer
            new_destination.save()

            messages.add_message(request, messages.SUCCESS, 'Destination {} successfully added!'.format(new_destination.name))

            if 'save_done' in destination_form.data:
                return redirect('register_self_complete')

    else:
        destination_form = DestinationForm()

    d = {
        'customer': customer,
        'destination_form': destination_form,
        'done_url': reverse('register_self_complete'),
        'home': home,
        'lovedone': False,
        'self': True,
    }
    return render(request, template, d)


@login_required
def register_self_complete(request, template='accounts/register_complete.html'):

    customer = request.user.get_customer()

    d = {
        'self': True,
        'lovedone': False,
        'customer': customer
    }
    return render(request, template, d)


@anonymous_required
def register_lovedone(request, gift=False, template='accounts/register.html'):
    if not settings.REGISTRATION_OPEN:
        messages.info(request, "Registration is temporarily closed. We are sorry for the inconvenience.")
        return redirect('homepage')

    errors = []
    error_count = []

    if request.method == 'GET':

        plan_selection = request.GET.get('plan', None)
        if plan_selection:
            request.session['plan'] = plan_selection

        register_form = CustomUserRegistrationForm(prefix='reg')
        customer_form = CustomerForm(prefix='cust', is_self=False)
        home_form = HomeForm(prefix='home')
        rider_form = RiderForm(prefix='rider')
    else:
        register_form = CustomUserRegistrationForm(request.POST, prefix='reg')
        customer_form = CustomerForm(request.POST, prefix='cust', is_self=False)
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

            authenticated_user = auth.authenticate(username=new_user.get_username(), password=register_form.cleaned_data['password1'])
            authenticated_user.backend = settings.AUTHENTICATION_BACKENDS[0]
            auth.login(request, authenticated_user)

            if gift:
                return redirect('register_lovedone_gift_payment')
            else:
                return redirect('register_lovedone_payment')
        else:
            errors = [register_form.errors, customer_form.errors, home_form.errors, rider_form.errors]
            error_count = sum([len(d) for d in errors])
    d = {
        'self': False,
        'lovedone': True,
        'register_form': register_form,
        'customer_form': customer_form,
        'plan_options': Plan.objects.filter(active=True),
        'home_form': home_form,
        'rider_form': rider_form,
        'errors': errors,
        'error_count': error_count,
        'gift': gift
        }
    return render(request, template, d)


@login_required
def register_lovedone_payment(request, gift=False, template='accounts/register_payment.html'):

    if request.user.is_staff:
        redirect('dashboard')

    customer = request.user.get_customer()
    errors = {}
    selected_plan = default_plan = None

    if request.method == 'POST':
        payment_form = PaymentForm(request.POST)
        if payment_form.is_valid():

            new_stripe_customer = payment_form.save()

            if payment_form.cleaned_data['same_card_for_both'] == '1':
                customer.subscription_account = customer.ride_account = new_stripe_customer
            else:
                customer.subscription_account = new_stripe_customer

            customer.plan = Plan.objects.get(pk=payment_form.cleaned_data['plan'])

            selected_plan = customer.plan

            create_stripe_customer = stripe.Customer.create(
                description='{} {}'.format(new_stripe_customer.first_name, new_stripe_customer.last_name),
                email=new_stripe_customer.email,
                source=payment_form.cleaned_data['stripe_token'],
                plan=customer.plan.stripe_id,
                metadata={
                    'customer': '{} [{}]'.format(customer.full_name, customer.pk),
                }
            )

            if customer.plan.signup_cost:
                stripe.Charge.create(
                    amount=customer.plan.signup_cost * 100,
                    currency="usd",
                    customer=create_stripe_customer.id
                )

            new_stripe_customer.stripe_id = create_stripe_customer.id

            customer.save()
            new_stripe_customer.save()

            messages.add_message(request, messages.SUCCESS, 'Plan selected, billing info saved')

            if payment_form.cleaned_data['same_card_for_both'] == '0':
                return redirect('register_payment_ride_account')
            return redirect('register_self_destinations')
        else:
            errors = payment_form.errors
            print
            print errors
            print

    else:
        plan_selection = request.session.get('plan', None)

        if plan_selection:
            print 'plan selection'
            selected_plan = Plan.objects.get(name=plan_selection.upper())
            default_plan = selected_plan
        else:
            print 'plan selection'
            default_plan = Plan.objects.get(name="SILVER")

        if customer.subscription_account:
            payment_form = PaymentForm(instance=customer.subscription_account)
        else:
            payment_form = PaymentForm(initial={
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                'same_card_for_both': 1,
                'plan': selected_plan
            })

    d = {
        'self': False,
        'lovedone': True,
        'customer': customer,
        'payment_form': payment_form,
        'plan_options': Plan.objects.filter(active=True).exclude(pk=Plan.UL_GIFT),
        'months': range(1, 13),
        'years': range(datetime.datetime.now().year, datetime.datetime.now().year + 15),
        'stripe_customer': customer.subscription_account,
        'soon': soon(),
        'errors': errors,
        'default_plan': default_plan,
        'gift': gift,
        'gift_plan': Plan.objects.get(name="UL_GIFT"),
        'selected_plan': selected_plan,
        'errors': errors
    }

    return render(request, template, d)


@login_required
def register_lovedone_preferences(request, template='accounts/register_preferences.html'):

    if request.user.is_staff:
        redirect('dashboard')

    user = request.user
    customer = request.user.get_customer()

    if request.method == 'GET':
        lovedone_form = LovedOnePreferencesForm(prefix='reg')
    else:
        lovedone_form = LovedOnePreferencesForm(request.POST, prefix='reg')

        if lovedone_form.is_valid():
            new_loved_one = lovedone_form.save(commit=False)
            new_loved_one.customer = customer
            new_loved_one.first_name = user.first_name
            new_loved_one.last_name = user.last_name
            new_loved_one.email = user.email
            new_loved_one.save()

            user.profile.receive_updates = new_loved_one.receive_updates
            user.profile.save()

            return redirect('register_lovedone_destinations')

    d = {
        'self': False,
        'lovedone': True,
        'lovedone_form': lovedone_form,
    }
    return render(request, template, d)


@login_required
def register_lovedone_destinations(request, template='accounts/register_destinations.html'):

    if request.user.is_staff:
        redirect('dashboard')

    customer = request.user.get_customer()
    home = customer.destination_set.filter(home=True).first()

    if request.method == "POST":
        destination_form = DestinationForm(request.POST)

        if destination_form.is_valid():

            new_destination = destination_form.save(commit=False)
            new_destination.customer = customer
            new_destination.save()

            messages.add_message(request, messages.SUCCESS, 'Destination {} successfully added!'.format(new_destination.name))

            if 'save_done' in destination_form.data:
                return redirect('register_lovedone_complete')

            return redirect('register_lovedone_destinations')

    else:
        destination_form = DestinationForm()

    d = {
        'customer': customer,
        'destination_form': destination_form,
        'done_url': reverse('register_lovedone_complete'),
        'home': home,
        'lovedone': True,
        'self': False,
    }
    return render(request, template, d)


@login_required
def register_lovedone_complete(request, template='accounts/register_complete.html'):

    customer = request.user.get_customer()

    d = {
        'self': False,
        'lovedone': True,
        'customer': customer
    }
    return render(request, template, d)


@login_required
def register_payment_ride_account(request, template='accounts/register_payment_ride_account.html'):

    if request.user.is_staff:
        redirect('dashboard')

    customer = request.user.get_customer()
    errors = {}

    if request.method == 'POST':
        payment_form = StripeCustomerForm(request.POST)
        if payment_form.is_valid():

            new_stripe_customer = payment_form.save()

            customer.ride_account = new_stripe_customer

            create_stripe_customer = stripe.Customer.create(
                description='{} {}'.format(new_stripe_customer.first_name, new_stripe_customer.last_name),
                email=new_stripe_customer.email,
                source=payment_form.cleaned_data['stripe_token'],
                metadata={
                    'customer': '{} [{}]'.format(customer.full_name, customer.pk),
                }
            )

            new_stripe_customer.stripe_id = create_stripe_customer.id

            customer.save()
            new_stripe_customer.save()

            messages.add_message(request, messages.SUCCESS, 'Credit card saved')

            return redirect('register_self_destinations')

        else:
            errors = payment_form.errors

    else:
        payment_form = StripeCustomerForm(initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email
        })

    d = {
        'customer': customer,
        'payment_form': payment_form,
        'months': range(1, 13),
        'years': range(datetime.datetime.now().year, datetime.datetime.now().year + 15),
        'soon': soon(),
        'errors': errors
    }

    return render(request, template, d)


@login_required
def register_payment_redirect(request):
    user = request.user
    if user.profile.on_behalf:
        return redirect('register_lovedone_payment')
    return redirect('register_self_payment')


@login_required
def profile(request, template='accounts/profile.html'):

    user = request.user

    if user.is_staff:
        return redirect('dashboard')

    customer = user.get_customer()

    if not customer.subscription_account:
        return redirect('register_payment_redirect')

    d = {
        'customer': customer,
        'riders': customer.riders.all(),
        'lovedone': user.profile.on_behalf
    }
    return render(request, template, d)


@login_required
def profile_edit(request, template='accounts/profile_edit.html'):

    user = request.user

    if user.is_staff:
        return redirect('dashboard')

    is_self = not user.profile.on_behalf
    customer = user.get_customer()
    home = customer.home
    rider = customer.rider

    if request.method == 'GET':
        customer_form = CustomerForm(prefix='cust', instance=customer, is_self=is_self)
        home_form = HomeForm(prefix='home', instance=home)
        rider_form = RiderForm(prefix='rider', instance=rider)
    else:
        customer_form = CustomerForm(request.POST, prefix='cust', instance=customer, is_self=is_self)
        home_form = HomeForm(request.POST, prefix='home', instance=home)
        rider_form = RiderForm(request.POST, prefix='rider', instance=rider)
        if all([
                customer_form.is_valid(),
                home_form.is_valid(),
                rider_form.is_valid()]):

            # populate and save customer
            customer_form.save(commit=False)
            customer.user_id = user.id
            customer_form.save()
            # populate and save home address
            home_form.save()
            # populate and save rider info
            if rider is None:
                rider_data = rider_form.cleaned_data
                if rider_data.get('first_name', None) or rider_data.get('last_name', None) or rider_data.get('mobile_phone', None):
                    rider = rider_form.save(commit=False)
                    rider.customer = customer
                    rider.save()
            else:
                rider.save()

            return redirect('profile')

    d = {
        'self': not user.profile.on_behalf,
        'lovedone': user.profile.on_behalf,
        'customer_form': customer_form,
        'home_form': home_form,
        'rider_form': rider_form
        }
    return render(request, template, d)


@login_required
def destination_edit(request, destination_id, template='accounts/destinations_edit.html'):

    user = request.user

    if user.is_staff:
        return redirect('dashboard')

    customer = user.get_customer()
    destination = get_object_or_404(Destination, pk=destination_id)

    if request.method == "POST":
        destination_form = DestinationForm(request.POST, instance=destination)

        if destination_form.is_valid():

            destination_form.save()

            messages.add_message(request, messages.SUCCESS, 'Destination {} successfully updated!'.format(customer, destination.name))
            return redirect('profile')

    else:
        destination_form = DestinationForm(instance=destination)

    d = {
        'customer': customer,
        'destination': destination,
        'destination_form': destination_form
    }

    return render(request, template, d)


def destination_add(request, template='accounts/destination_add.html'):

    if request.user.is_staff:
        redirect('dashboard')

    user = request.user
    customer = user.get_customer()

    if request.method == "POST":
        destination_form = DestinationForm(request.POST)

        if destination_form.is_valid():

            new_destination = destination_form.save(commit=False)
            new_destination.customer = customer
            new_destination.save()

            messages.add_message(request, messages.SUCCESS, 'Destination {} successfully added!'.format(new_destination.name))
            return redirect('profile')

    else:
        destination_form = DestinationForm()

    d = {
        'customer': customer,
        'destination_form': destination_form
    }

    return render(request, template, d)


def destination_delete(request, destination_id):

    if request.user.is_staff:
        redirect('dashboard')

    destination = get_object_or_404(Destination, pk=destination_id)
    deleted = destination.delete()
    if deleted:
        messages.add_message(request, messages.SUCCESS, 'Destination successfully deleted')

    return redirect('profile')
