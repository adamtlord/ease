import stripe

from django.core.cache import cache


def get_stripe_subscription(customer):
    cache_key = '{}_subscription'.format(customer.subscription_account.stripe_id)
    cached_subscription = cache.get(cache_key)
    subscription = ''

    if not cached_subscription:

        stripe_customer = stripe.Customer.retrieve(customer.subscription_account.stripe_id)

        if stripe_customer is not None:

            customer_subscription = stripe_customer.subscriptions.data[0]
            cache.set(cache_key, customer_subscription, 3600)
            subscription = customer_subscription

        else:
            subscription = None
    else:

        subscription = cached_subscription

    return subscription
