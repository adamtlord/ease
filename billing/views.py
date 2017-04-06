import datetime
import stripe

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect

from billing.forms import PaymentForm, StripeCustomerForm
from common.utils import soon


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
def customer_ride_account_edit(request, template="billing/customer_ride_account_edit.html"):

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
                        customer.save()
                        stripe_customer.save()

                        messages.add_message(request, messages.SUCCESS, 'Billing info saved')

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
                stripe_cust.metadata = {'customer': '{} [{}]'.format(customer.full_name, customer.pk)}
                try:
                    stripe_cust.save()
                    payment_form.save()
                    messages.add_message(request, messages.SUCCESS, 'Billing info updated')

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
