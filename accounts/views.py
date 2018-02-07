import datetime
import stripe

from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import smart_str

from common.decorators import anonymous_required
from accounts.forms import (CustomUserRegistrationForm, CustomUserForm,
                            CustomerForm, RiderForm, GroupRegistrationForm,
                            GroupContactRegistrationForm, GroupCustomerForm)
from accounts.helpers import send_welcome_email, send_subscription_receipt_email, create_customer_subscription
from accounts.models import Customer
from billing.models import Plan, Balance, StripeCustomer, Gift, GroupMembership
from billing.forms import PaymentForm, StripeCustomerForm, GiftForm, AddFundsForm
from billing.utils import get_stripe_subscription, get_customer_stripe_accounts
from common.utils import soon
from concierge.models import Touch
from rides.models import Destination
from rides.forms import DestinationForm, HomeForm, GroupAddressForm

stripe.api_key = settings.STRIPE_SECRET_KEY


@anonymous_required
def register_self(request, template='accounts/register.html'):

    errors = []

    if not settings.REGISTRATION_OPEN:
        messages.info(request, "Registration is temporarily closed. We are sorry for the inconvenience.")
        return redirect('homepage')

    if request.method == 'GET':

        plan_selection = request.GET.get('plan', None)
        if plan_selection:
            request.session['plan'] = plan_selection

        gift_flow = request.GET.get('gift', None)
        if gift_flow:
            request.session['gift'] = True

        request.session['lovedone'] = False
        request.session['self'] = True

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
            new_customer.plan = Plan.objects.get(pk=Plan.DEFAULT)
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

            # Send welcome email
            send_welcome_email(new_user)

            if request.session.get('gift', False):
                return redirect('register_add_funds')

            # Skip preferences for now because Lyft doesn't offer that
            # 2016-11-23
            return redirect('register_self_payment')
        else:
            errors = [register_form.errors, customer_form.errors, home_form.errors, rider_form.errors]

    d = {
        'self': True,
        'lovedone': False,
        'register_form': register_form,
        'customer_form': customer_form,
        'home_form': home_form,
        'rider_form': rider_form,
        'errors': errors
    }
    return render(request, template, d)


@login_required
def register_add_funds(request, template='accounts/register_add_funds.html'):
    customer = request.user.get_customer()
    errors = {}
    card_errors = None
    is_self = request.session.get('self', False)
    lovedone = request.session.get('lovedone', True)
    gift_flow = request.session.get('gift', False)

    if request.method == 'POST':
        payment_form = AddFundsForm(request.POST)
        gift_form = GiftForm(request.POST, prefix="gift")

        if payment_form.is_valid() and gift_form.is_valid():
            try:
                # Add a new credit card/Stripe customer
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
                            customer.balance.amount = charge_amount
                            customer.balance.user_updated = request.user
                            customer.balance.stripe_customer = stripe_customer
                            customer.balance.save()

                        except Balance.DoesNotExist:
                            new_balance = Balance(
                                amount=charge_amount,
                                customer=customer,
                                user_created=request.user,
                                stripe_customer=stripe_customer
                            )
                            new_balance.save()

                        new_gift = False
                        if request.POST.get('is_gift', False):
                            new_gift = gift_form.save(commit=False)
                            new_gift.email = stripe_customer.email
                            new_gift.customer = customer
                            new_gift.amount = request.POST['amount']
                            new_gift.save()

                            gift_note = 'Received a gift of ${} from {}'.format(charge_amount, new_gift.first_name, new_gift.last_name)
                            if new_gift.relationship:
                                gift_note += ' ({})'.format(new_gift.relationship)

                            gift_touch = Touch(
                                customer=customer,
                                date=timezone.now(),
                                type=Touch.GIFT,
                                notes=gift_note
                            )
                            gift_touch.full_clean()
                            gift_touch.save()

                        if not hasattr(customer, 'subscription'):
                            create_customer_subscription(customer)

                        # Customer has a balance, consider active
                        customer.is_active = True
                        customer.save()

                        customer_str = 'your' if is_self else '{}\'s'.format(customer.first_name)
                        success_message = '${} successfully added to {} account'.format(charge_amount, customer_str)

                        messages.add_message(
                            request,
                            messages.SUCCESS,
                            success_message
                        )
                        funds_touch = Touch(
                            customer=customer,
                            date=timezone.now(),
                            type=Touch.FUNDS,
                            notes='Added ${} to account'.format(charge_amount)
                        )
                        funds_touch.full_clean()
                        funds_touch.save()

                        return redirect('register_lovedone_payment')

            # catch Stripe card validation errors
            except stripe.error.CardError as ex:
                card_errors = 'We encountered a problem processing your credit card. The error we received was "{}" Please try a different card, or contact your bank.'.format(ex.json_body['error']['message'])

            # catch any other type of error
            except Exception as ex:
                card_errors = 'We had trouble processing your credit card. You have not been charged. Please try again, or give us a call at 1-866-626-9879.'

        else:
            errors = payment_form.errors

    else:
        payment_form = AddFundsForm(
            initial={
                'email': customer.user.email,
                'first_name': customer.user.first_name,
                'last_name': customer.user.last_name,
            })
        gift_form = GiftForm(
            prefix="gift",
            initial={
                'first_name': customer.user.first_name,
                'last_name': customer.user.last_name,
                'relationship': customer.user.profile.relationship
            })

    d = {
        'self': is_self,
        'lovedone': lovedone,
        'customer': customer,
        'payment_form': payment_form,
        'gift_form': gift_form,
        'months': range(1, 13),
        'years': range(datetime.datetime.now().year, datetime.datetime.now().year + 15),
        'soon': soon(),
        'errors': errors,
        'card_errors': card_errors,
        'gift': gift_flow
    }

    return render(request, template, d)


@login_required
def register_self_payment(request, template='accounts/register_payment.html'):

    if request.user.is_staff:
        redirect('dashboard')

    customer = request.user.get_customer()
    errors = {}
    card_errors = None

    if request.method == 'POST':
        if 'skip' in request.POST:
            messages.success(request, 'Yay! You now have ${} in rides.'.format(customer.balance.amount))
            return redirect('register_self_destinations')

        if customer.subscription_account:

            if customer.destinations.count():
                messages.warning(request, 'This form has already been submitted. To make changes to your subscription, please edit your profile or contact customer service at 1-866-626-9879 or <a href="mailto:helloa@arriverides.com">hello@arriverides.com</a>.'.format(reverse('profile')))
                return redirect('profile')

            messages.warning(request, 'This form has already been submitted. To make changes to your subscription, please <a href={}>visit your profile</a> or contact customer service at 1-866-626-9879 or <a href="mailto:helloa@arriverides.com">hello@arriverides.com</a>.'.format(reverse('profile')))
            return redirect('register_self_destinations')

        payment_form = PaymentForm(request.POST)

        if payment_form.is_valid():

            try:
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
                    # create our stripe customer
                    new_stripe_customer = payment_form.save()
                    customer.subscription_account = customer.ride_account = new_stripe_customer
                    # set our customer's plan
                    customer.plan = Plan.objects.get(pk=payment_form.cleaned_data['plan'])
                    selected_plan = customer.plan
                    # if chosen plan has an upfront cost, create an invoice line-item
                    if customer.plan.signup_cost:
                        # create signup invoice item
                        # this is only charging $25 for bronze plan. Needs to be $30.
                        # signup_cost = int((customer.plan.signup_cost - customer.plan.monthly_cost) * 100)
                        signup_cost = int(customer.plan.signup_cost * 100)
                        stripe.InvoiceItem.create(
                            customer=create_stripe_customer.id,
                            amount=signup_cost,
                            currency="usd",
                            description="Initial signup fee",
                            idempotency_key='{}{}'.format(customer.id, datetime.datetime.now().isoformat())
                        )

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
                    # now attach the customer to a plan
                    stripe.Subscription.create(
                        customer=create_stripe_customer.id,
                        plan=customer.plan.stripe_id,
                        idempotency_key='{}{}'.format(customer.id, datetime.datetime.now().isoformat()),
                        coupon=coupon_code
                    )
                    # store the customer's stripe id in their record
                    new_stripe_customer.stripe_id = create_stripe_customer.id
                    # activate customer, save everything
                    customer.is_active = True
                    customer.save()
                    new_stripe_customer.save()

                    send_subscription_receipt_email(request.user)

                    # send_new_customer_email(request.user)

                    messages.add_message(request, messages.SUCCESS, 'Congratulations! Plan selected, billing info securely saved.')

                    request.session['payment_complete'] = True

                    if request.session.get('next'):
                        next_url = request.session.get('next')
                        del request.session['next']
                        return redirect(next_url)

                    return redirect('register_self_destinations')

            # catch Stripe card validation errors
            except stripe.error.CardError as ex:
                card_errors = 'We encountered a problem processing your credit card. The error we received was "{}" Please try a different card, or contact your bank.'.format(ex.json_body['error']['message'])

            # catch any other type of error
            except Exception as ex:
                card_errors = 'We had trouble processing your credit card. You have not been charged. Please try again, or give us a call at 1-866-626-9879.'

        else:
            errors = payment_form.errors

    else:

        if customer.subscription_account:
            payment_form = PaymentForm(instance=customer.subscription_account, initial={
                'plan': customer.plan.id
            })

        else:
            payment_form = PaymentForm(initial={
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                'same_card_for_both': 1,
            })

    d = {
        'self': True,
        'lovedone': False,
        'customer': customer,
        'payment_form': payment_form,
        'months': range(1, 13),
        'years': range(datetime.datetime.now().year, datetime.datetime.now().year + 15),
        'stripe_customer': customer.subscription_account,
        'soon': soon(),
        'errors': errors,
        'card_errors': card_errors
    }

    return render(request, template, d)


@login_required
def register_self_destinations(request, template='accounts/register_destinations.html'):
    errors = {}
    payment_complete = request.session.get('payment_complete')
    if payment_complete:
        del request.session['payment_complete']

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

            messages.add_message(request, messages.SUCCESS, 'Destination {} successfully added!'.format(smart_str(new_destination.name)))

            if 'save_done' in destination_form.data:
                return redirect('register_self_complete')
        else:
            errors = destination_form.errors

    else:
        destination_form = DestinationForm()

    d = {
        'customer': customer,
        'destination_form': destination_form,
        'done_url': reverse('register_self_complete'),
        'home': home,
        'lovedone': False,
        'self': True,
        'payment_complete': payment_complete,
        'errors': errors,
        'geolocate': customer.home
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

    gift_flow = request.GET.get('gift', None)

    if request.method == 'GET':

        plan_selection = request.GET.get('plan', None)
        if plan_selection:
            request.session['plan'] = plan_selection

        if gift_flow:
            request.session['gift'] = True

        request.session['lovedone'] = True
        request.session['self'] = False

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
            new_user.profile.phone = register_form.cleaned_data['phone']
            new_user.profile.save()

            send_welcome_email(new_user)

            authenticated_user = auth.authenticate(username=new_user.get_username(), password=register_form.cleaned_data['password1'])
            authenticated_user.backend = settings.AUTHENTICATION_BACKENDS[0]
            auth.login(request, authenticated_user)

            if request.session.get('gift', False):
                return redirect('register_add_funds')
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
        'gift': gift_flow
    }

    return render(request, template, d)


@login_required
def register_lovedone_payment(request, gift=False, template='accounts/register_payment.html'):

    if request.user.is_staff:
        redirect('dashboard')

    customer = request.user.get_customer()
    errors = {}
    card_errors = None
    gift_flow = request.session.get('gift', False)

    if request.method == 'POST':

        if customer.subscription_account:

            if customer.destinations.count():
                messages.warning(request, 'This form has already been submitted. To make changes to your subscription, please edit your profile or contact customer service at 1-866-626-9879 or <a href="mailto:helloa@arriverides.com">hello@arriverides.com</a>.'.format(reverse('profile')))
                return redirect('profile')

            messages.warning(request, 'This form has already been submitted. To make changes to your subscription, please <a href={}>visit your profile</a> or contact customer service at 1-866-626-9879 or <a href="mailto:helloa@arriverides.com">hello@arriverides.com</a>.'.format(reverse('profile')))
            return redirect('register_self_destinations')

        payment_form = PaymentForm(request.POST)

        if payment_form.is_valid():

            try:
                # create new stripe customer
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

                    # set our customer's plan
                    if payment_form.cleaned_data['same_card_for_both'] == '1':
                        customer.subscription_account = customer.ride_account = new_stripe_customer
                    else:
                        customer.subscription_account = new_stripe_customer

                    customer.plan = Plan.objects.get(pk=payment_form.cleaned_data['plan'])

                    selected_plan = customer.plan

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

                    # store the customer's stripe id in their record
                    new_stripe_customer.stripe_id = create_stripe_customer.id
                    # activate customer, save everything
                    customer.is_active = True
                    customer.save()
                    new_stripe_customer.save()

                    # if the customer already has a gift balance, let the gift balance take care of the
                    # subscription fees. No need to add a Stripe subscription here.
                    if not customer.has_funds:
                        # now attach the customer to a plan
                        stripe.Subscription.create(
                            customer=create_stripe_customer.id,
                            plan=customer.plan.stripe_id,
                            idempotency_key='{}{}'.format(customer.id, datetime.datetime.now().isoformat()),
                            coupon=coupon_code
                        )
                        send_subscription_receipt_email(request.user)


                    # send_new_customer_email(request.user)

                    messages.add_message(request, messages.SUCCESS, 'Plan selected, billing info saved')

                    if payment_form.cleaned_data['same_card_for_both'] == '0':

                        return redirect('register_payment_ride_account')

                    request.session['payment_complete'] = True

                    if request.session.get('next'):
                        next_url = request.session.get('next')
                        del request.session['next']
                        return redirect(next_url)

                    return redirect('register_lovedone_destinations')

            # catch Stripe card validation errors
            except stripe.error.CardError as ex:
                card_errors = 'We encountered a problem processing your credit card. The error we received was "{}" Please try a different card, or contact your bank.'.format(ex.json_body['error']['message'])

            # catch any other type of error
            except Exception as ex:
                card_errors = 'We had trouble processing your credit card. You have not been charged. Please try again, or give us a call at 1-866-626-9879.'

        # form is invalid
        else:
            errors = payment_form.errors

    # GET
    else:
        # set defaults and initials
        if customer.subscription_account:
            payment_form = PaymentForm(instance=customer.subscription_account, initial={
                'plan': customer.plan.id
            })

        else:
            payment_form = PaymentForm(initial={
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                'same_card_for_both': 1,
            })
    # context
    d = {
        'self': False,
        'lovedone': True,
        'customer': customer,
        'payment_form': payment_form,
        'months': range(1, 13),
        'years': range(datetime.datetime.now().year, datetime.datetime.now().year + 15),
        'stripe_customer': customer.subscription_account,
        'soon': soon(),
        'errors': errors,
        'gift_plan': Plan.objects.get(name="INTRO_GIFT"),
        'errors': errors,
        'card_errors': card_errors,
        'gift': gift_flow
    }

    return render(request, template, d)


@login_required
def register_lovedone_destinations(request, template='accounts/register_destinations.html'):
    if request.user.is_staff:
        redirect('dashboard')

    errors = {}
    customer = request.user.get_customer()
    home = customer.destination_set.filter(home=True).first()

    if request.method == "POST":
        destination_form = DestinationForm(request.POST)

        if destination_form.is_valid():

            new_destination = destination_form.save(commit=False)
            new_destination.customer = customer
            new_destination.save()

            messages.add_message(request, messages.SUCCESS, 'Destination {} successfully added!'.format(smart_str(new_destination.name)))

            if 'save_done' in destination_form.data:
                return redirect('register_lovedone_complete')

            return redirect('register_lovedone_destinations')
        else:
            errors = destination_form.errors

    else:
        destination_form = DestinationForm()

    d = {
        'customer': customer,
        'destination_form': destination_form,
        'done_url': reverse('register_lovedone_complete'),
        'home': home,
        'lovedone': True,
        'self': False,
        'errors': errors,
        'geolocate': customer.home
    }
    return render(request, template, d)


@login_required
def register_lovedone_complete(request, template='accounts/register_complete.html'):

    customer = request.user.get_customer()
    if 'gift' in request.session:
        del request.session['gift']

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
    card_errors = None

    if request.method == 'POST':

        if customer.ride_account:

            if customer.destinations.count():
                messages.warning(request, 'This form has already been submitted. To make changes to your subscription, please edit your profile or contact customer service at 1-866-626-9879 or <a href="mailto:helloa@arriverides.com">hello@arriverides.com</a>.'.format(reverse('profile')))
                return redirect('profile')

            messages.warning(request, 'This form has already been submitted. To make changes to your subscription, please <a href={}>visit your profile</a> or contact customer service at 1-866-626-9879 or <a href="mailto:helloa@arriverides.com">hello@arriverides.com</a>.'.format(reverse('profile')))
            return redirect('register_self_destinations')

        payment_form = StripeCustomerForm(request.POST)

        if payment_form.is_valid():

            try:
                # create new stripe customer
                create_stripe_customer = stripe.Customer.create(
                    description='{} {}'.format(payment_form.cleaned_data['first_name'], payment_form.cleaned_data['last_name']),
                    email=payment_form.cleaned_data['email'],
                    source=payment_form.cleaned_data['stripe_token'],
                    metadata={
                        'customer': '{} [{}]'.format(customer.full_name, customer.pk),
                    }
                )

                if create_stripe_customer:
                    # create our stripe customer
                    new_stripe_customer = payment_form.save()
                    customer.ride_account = new_stripe_customer

                    # store the customer's stripe id in their record
                    new_stripe_customer.stripe_id = create_stripe_customer.id

                    # save everything
                    customer.save()
                    new_stripe_customer.save()

                    messages.add_message(request, messages.SUCCESS, 'Credit card saved')

                    return redirect('register_lovedone_destinations')

            except stripe.error.CardError as ex:
                card_errors = 'We encountered a problem processing your credit card. The error we received was "{}" Please try a different card, or contact your bank.'.format(ex.json_body['error']['message'])

            except Exception as ex:
                card_errors = 'We had trouble processing your credit card. You have not been charged. Please try again, or give us a call at 1-866-626-9879.'

        else:
            errors = payment_form.errors

    else:
        if customer.ride_account:
            payment_form = StripeCustomerForm(instance=customer.ride_account)

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
        'errors': errors,
        'card_errors': card_errors
    }

    return render(request, template, d)


@anonymous_required
def register_group(request, template='accounts/register_group.html'):

    errors = []
    error_count = []

    if request.method == 'GET':
        register_form = GroupContactRegistrationForm(prefix='reg')
        group_form = GroupRegistrationForm(prefix='group')
        address_form = GroupAddressForm(prefix='home')
    else:
        register_form = GroupContactRegistrationForm(request.POST, prefix='reg')
        group_form = GroupRegistrationForm(request.POST, prefix='group')
        address_form = GroupAddressForm(request.POST, prefix='home')

        if all([
            register_form.is_valid(),
            group_form.is_valid(),
            address_form.is_valid()
        ]):
            # save user
            new_user = register_form.save(request)
            new_user.is_group_admin = True
            new_user.save()
            # save group
            new_group = group_form.save()
            new_group.user = new_user
            new_group.display_name = new_group.name
            new_group.save()
            # create dummy customer for group
            new_customer = Customer.objects.create(
                first_name=new_group.name,
                last_name="Group",
                is_active=True,
                user=new_user
            )
            # populate and save home address
            group_address = address_form.save(commit=False)
            group_address.customer = new_customer
            group_address.home = True
            group_address.save()
            # attach address to group membership
            new_group.address = group_address
            new_group.save()
            # populate user profile
            new_user.profile.registration_complete = True
            new_user.profile.on_behalf = True
            new_user.profile.phone = register_form.cleaned_data['phone']
            new_user.profile.save()
            # log in new user
            authenticated_user = auth.authenticate(username=new_user.get_username(), password=register_form.cleaned_data['password1'])
            authenticated_user.backend = settings.AUTHENTICATION_BACKENDS[0]
            auth.login(request, authenticated_user)

            # TODO
            # send_welcome_group_email(new_user)

            return redirect('register_group_payment')

        else:
            errors = [register_form.errors, group_form.errors, address_form.errors]
            error_count = sum([len(d) for d in errors])

    d = {
        'register_form': register_form,
        'group_form': group_form,
        'address_form': address_form,
        'errors': errors,
        'error_count': error_count,
    }

    return render(request, template, d)


@login_required
def register_group_payment(request, gift=False, template='accounts/register_group_payment.html'):

    try:
        group = request.user.groupmembership
    except GroupMembership.DoesNotExist:
        messages.error(request, 'You must be the administrator of a Group Membership to view that page.')
        return redirect('profile')

    errors = {}
    card_errors = None

    if request.method == 'POST':

        payment_form = PaymentForm(request.POST)

        if payment_form.is_valid():
            try:
                # create new stripe customer
                create_stripe_customer = stripe.Customer.create(
                    description='{} {}'.format(payment_form.cleaned_data['first_name'], payment_form.cleaned_data['last_name']),
                    email=payment_form.cleaned_data['email'],
                    source=payment_form.cleaned_data['stripe_token'],
                    metadata={
                        'group membership': '{} {}'.format(group, group.pk)
                    }
                )

                if create_stripe_customer:
                    # create our stripe customer
                    new_stripe_customer = payment_form.save()

                    # set our customer's plan
                    group.ride_account = new_stripe_customer

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

                    # store the customer's stripe id in their record
                    new_stripe_customer.stripe_id = create_stripe_customer.id
                    group.save()
                    new_stripe_customer.save()

                    messages.add_message(request, messages.SUCCESS, 'Group billing info saved')

                    request.session['payment_complete'] = True

                    return redirect('register_group_riders')

            # catch Stripe card validation errors
            except stripe.error.CardError as ex:
                card_errors = 'We encountered a problem processing your credit card. The error we received was "{}" Please try a different card, or contact your bank.'.format(ex.json_body['error']['message'])

            # catch any other type of error
            except Exception as ex:
                card_errors = 'We had trouble processing your credit card. You have not been charged. Please try again, or give us a call at 1-866-626-9879.'

        # form is invalid
        else:
            errors = payment_form.errors

    # GET
    else:
        # set defaults and initials
        if group.ride_account:
            payment_form = PaymentForm(instance=group.ride_account, initial={
                'plan': group.plan.id
            })

        else:
            payment_form = PaymentForm(initial={
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
            })
    d = {
        'group': group,
        'payment_form': payment_form,
        'months': range(1, 13),
        'years': range(datetime.datetime.now().year, datetime.datetime.now().year + 15),
        'stripe_customer': group.ride_account,
        'soon': soon(),
        'errors': errors,
        'card_errors': card_errors,
    }

    return render(request, template, d)


@login_required
def register_group_riders(request, template='accounts/register_group_riders.html'):

    try:
        group = request.user.groupmembership
    except GroupMembership.DoesNotExist:
        messages.error(request, 'You must be the administrator of a Group Membership to view that page.')
        return redirect('profile')

    errors = []
    error_count = []
    if request.method == 'POST':
        customer_form = GroupCustomerForm(request.POST)
        if customer_form.is_valid():
            cd = customer_form.cleaned_data
            # create user for customer based on group's user
            new_user = group.user
            new_user.pk = None
            # This is... uh... fake. It won't be used because the account is managed by the group
            new_user.email = '{}_{}_group{}@arriverides.com'.format(cd['first_name'], cd['last_name'], group.id)
            new_user.save()

            # populate and save customer
            new_customer = customer_form.save(commit=False)
            new_customer.user = new_user
            new_customer.registered_by = request.user
            new_customer.intro_call = True
            new_customer.is_active = True
            new_customer.group_membership = group
            new_customer.ride_account = group.ride_account
            new_customer.subscription_account = group.subscription_account
            new_customer.save()

            # copy the group's home address to use as the customer's home address
            if group.address and group.default_user_address:
                customer_home = group.address
                customer_home.pk = None
                customer_home.customer = new_customer
                customer_home.home = True
                customer_home.save()

            messages.add_message(request, messages.SUCCESS, 'Customer {} successfully added!'.format(new_customer))
            if 'save_done' in customer_form.data:
                return redirect('register_group_complete')
            return redirect('register_group_riders')

        else:
            errors = customer_form.errors
            error_count = sum([len(d) for d in errors])
    else:
        customer_form = GroupCustomerForm()

    d = {
        'group': group,
        'customer_form': customer_form,
        'errors': errors,
        'error_count': error_count,
        'done_url': reverse('register_group_complete'),
    }
    return render(request, template, d)


@login_required
def register_group_complete(request, template='accounts/register_group_complete.html'):

    try:
        group = request.user.groupmembership
    except GroupMembership.DoesNotExist:
        messages.error(request, 'You must be the administrator of a Group Membership to view that page.')
        return redirect('profile')

    d = {
        'group': group
    }
    return render(request, template, d)


@login_required
def register_payment_redirect(request):
    user = request.user
    customer = user.get_customer()
    next_param = request.GET.get('next')
    if next_param:
        request.session['next'] = next_param

    if customer.subscription_account:
        return redirect('customer_subscription_account_edit')
    else:
        if user.profile.on_behalf:
            return redirect('register_lovedone_payment')
        return redirect('register_self_payment')


@login_required
def profile(request, template='accounts/profile.html'):

    if 'gift' in request.session:
        del request.session['gift']

    user = request.user
    if user.is_group_admin:
        return redirect('group_profile')

    if user.is_staff:
        return redirect('dashboard')

    try:
        customer = user.get_customer()
    except Customer.DoesNotExist:
        messages.error(request, "That username is not associated with a customer.")
        auth.logout(request)
        return redirect('auth_login')

    subscription = None

    if customer.subscription_account and customer.subscription_account.stripe_id:
        subscription = get_stripe_subscription(customer)

    d = {
        'customer': customer,
        'subscription': subscription,
        'riders': customer.riders.all(),
        'lovedone': user.profile.on_behalf,

    }
    return render(request, template, d)


@login_required
def group_profile(request, template='accounts/group_profile.html'):

    try:
        group = request.user.groupmembership
    except GroupMembership.DoesNotExist:
        messages.error(request, 'You must be the administrator of a Group Membership to view that page.')
        return redirect('profile')

    d = {
        'group': group,
        'customers': group.customer_set.all()
    }

    return render(request, template, d)


@login_required
def profile_edit(request, template='accounts/profile_edit.html'):

    user = request.user
    errors = []

    if user.is_staff:
        return redirect('dashboard')

    is_self = not user.profile.on_behalf
    customer = user.get_customer()
    home = customer.home
    rider = customer.rider

    if request.method == 'GET':
        user_form = CustomUserForm(prefix='reg', instance=user)
        customer_form = CustomerForm(prefix='cust', instance=customer, is_self=is_self)
        home_form = HomeForm(prefix='home', instance=home)
        rider_form = RiderForm(prefix='rider', instance=rider)
    else:
        user_form = CustomUserForm(request.POST, prefix='reg', instance=user)
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

        else:
            errors = [customer_form.errors, home_form.errors, rider_form.errors]

    d = {
        'self': not user.profile.on_behalf,
        'lovedone': user.profile.on_behalf,
        'customer_form': customer_form,
        'user_form': user_form,
        'home_form': home_form,
        'rider_form': rider_form,
        'errors': errors
        }
    return render(request, template, d)


@login_required
def profile_add_funds(request, template='accounts/profile_add_funds.html'):
    user = request.user

    if user.is_staff:
        return redirect('dashboard')

    customer = user.get_customer()
    customer_stripe_accounts = get_customer_stripe_accounts(customer)
    errors = {}
    card_errors = None

    if request.method == 'POST':
        payment_form = AddFundsForm(request.POST, unrequire=request.POST['funds_source'] != "new")
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
                        new_balance = Balance(
                            amount=charge_amount,
                            customer=customer,
                            user_created=request.user,
                            stripe_customer=stripe_customer
                        )
                        new_balance.save()

                    # Create a customer subscription so we can track drawing down their balance monthly
                    if not hasattr(customer, 'subscription'):
                        create_customer_subscription(customer)

                    # make sure customer is marked active
                    customer.is_active = True
                    customer.save()

                    success_message = '${} successfully added to {}\'s account'.format(charge_amount, customer)

                    messages.add_message(
                        request,
                        messages.SUCCESS,
                        success_message
                    )
                    funds_touch = Touch(
                        customer=customer,
                        date=timezone.now(),
                        type=Touch.FUNDS,
                        notes='Added ${} to account'.format(charge_amount)
                    )
                    funds_touch.full_clean()
                    funds_touch.save()

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
        payment_form = AddFundsForm(
            initial={
                'email': user.email if customer.user.profile.on_behalf else customer.email,
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'billing_zip': customer.home.zip_code
            }
        )
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
        'customer_stripe_accounts': customer_stripe_accounts,
        'lovedone': user.profile.on_behalf
    }

    return render(request, template, d)


def gift_login(request, template='accounts/gift_login.html'):

    login_form = auth.forms.AuthenticationForm(request)
    matching_customers = []
    match = True

    if request.method == 'POST':
        phone = request.POST['phone_lookup']
        matching_customers = Customer.objects.filter(
            Q(mobile_phone=phone) |
            Q(home_phone=phone) |
            Q(user__profile__phone=phone)
        ).distinct()

        if len(matching_customers) == 1:
            matching_customer = matching_customers[0];
            messages.success(request, '<strong>Success!</strong> We found {}.'.format(matching_customer))
            return redirect('gift_purchase', matching_customer.id)

        else:
            match = False

    d = {
        'login_form': login_form,
        'matching_customers': matching_customers,
        'match': match
    }

    return render(request, template, d)


def gift_purchase(request, customer_id, template='accounts/gift_purchase.html'):

    customer = get_object_or_404(Customer, pk=customer_id)
    errors = {}
    card_errors = None

    if request.method == 'POST':
        payment_form = StripeCustomerForm(request.POST, unrequire=False)
        gift_form = GiftForm(request.POST, prefix="gift")

        if all([
                payment_form.is_valid(),
                gift_form.is_valid(),
                request.POST.get('amount', False)]):

            try:
                # Add a new credit card/Stripe customer

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
                            customer.balance.save()

                        except Balance.DoesNotExist:
                            new_balance = Balance(amount=charge_amount, customer=customer)
                            new_balance.save()

                        success_message = '${} successfully added to {}\'s account'.format(charge_amount, customer)

                        new_gift = gift_form.save(commit=False)
                        new_gift.email = stripe_customer.email
                        new_gift.customer = customer
                        new_gift.amount = request.POST['amount']
                        new_gift.first_name = stripe_customer.first_name
                        new_gift.last_name = stripe_customer.last_name
                        new_gift.save()

                        # make sure customer is active
                        customer.is_active = True
                        customer.save()

                        success_message += ' as a gift from {} {}'.format(new_gift.first_name, new_gift.last_name)

                        gift_note = 'Received a gift of ${} from {}'.format(charge_amount, new_gift.first_name, new_gift.last_name)
                        if new_gift.relationship:
                            gift_note += ' ({})'.format(new_gift.relationship)

                        gift_touch = Touch(
                            customer=customer,
                            date=timezone.now(),
                            type=Touch.GIFT,
                            notes=gift_note
                        )
                        gift_touch.full_clean()
                        gift_touch.save()

                        if not hasattr(customer, 'subscription'):
                            create_customer_subscription(customer)

                        funds_touch = Touch(
                            customer=customer,
                            date=timezone.now(),
                            type=Touch.FUNDS,
                            notes='Added ${} to account'.format(charge_amount)
                        )
                        funds_touch.full_clean()
                        funds_touch.save()

                        return redirect('gift_purchase_receipt', customer.id, new_gift.id)

            # catch Stripe card validation errors
            except stripe.error.CardError as ex:
                card_errors = 'We encountered a problem processing your credit card. The error we received was "{}" Please try a different card, or contact your bank.'.format(ex.json_body['error']['message'])

            # catch any other type of error
            except Exception as ex:
                card_errors = 'We had trouble processing your credit card. You have not been charged. Please try again, or give us a call at 1-866-626-9879.'

        else:
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
    }
    return render(request, template, d)


def gift_purchase_receipt(request, customer_id, gift_id, template='accounts/gift_purchase_receipt.html'):
    customer = get_object_or_404(Customer, pk=customer_id)
    gift = get_object_or_404(Gift, pk=gift_id)

    d = {
        'customer': customer,
        'gift': gift
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

            messages.add_message(request, messages.SUCCESS, 'Destination {} successfully updated!'.format(smart_str(customer), smart_str(destination.name)))
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

            messages.add_message(request, messages.SUCCESS, 'Destination {} successfully added!'.format(smart_str(new_destination.name)))
            return redirect('profile')

    else:
        destination_form = DestinationForm()

    d = {
        'customer': customer,
        'destination_form': destination_form,
        'geolocate': customer.home
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


def password_validate(request):
    from django.contrib.auth.password_validation import validate_password

    password = request.GET.get('pswd', None)
    if password:
        try:
            validate_password(password)
            response = JsonResponse({'valid': True})
            return response
        except ValidationError as errors:
            response = JsonResponse({'valid': False, 'errors': [str(error) for error in errors]})
            return response
    return JsonResponse({'valid': False})
