import datetime
import stripe

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from accounts.models import Customer
from billing.forms import PaymentForm, StripeCustomerForm
from common.utils import soon


@login_required
def customer_subscription_account_edit(request, template="billing/customer_subscription_account_edit.html"):

    customer = request.user.get_customer()
    errors = {}

    if request.method == 'POST':
        payment_form = PaymentForm(request.POST, instance=customer.subscription_account)
        if payment_form.is_valid():

            stripe_customer = payment_form.save()

            if payment_form.cleaned_data['same_card_for_both'] == '1':
                customer.subscription_account = customer.ride_account = stripe_customer
            else:
                customer.subscription_account = stripe_customer

            if payment_form.cleaned_data['stripe_token']:
                create_stripe_customer = stripe.Customer.create(
                    description='{} {}'.format(stripe_customer.first_name, stripe_customer.last_name),
                    email=stripe_customer.email,
                    source=payment_form.cleaned_data['stripe_token'],
                    plan=customer.plan.stripe_id,
                    metadata={
                        'customer': '{} {}'.format(customer.full_name, customer.pk)
                    }
                )

                stripe_customer.stripe_id = create_stripe_customer.id

            customer.save()
            stripe_customer.save()

            messages.add_message(request, messages.SUCCESS, 'Plan selected, billing info saved')

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
                    }
                )

                stripe_customer.stripe_id = create_stripe_customer.id

            customer.save()
            stripe_customer.save()

            messages.add_message(request, messages.SUCCESS, 'Credit card saved')

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
