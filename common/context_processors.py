from django.conf import settings


def global_settings(request):
    return {
        'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
        'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLISHABLE_KEY,
        'DEBUG': settings.DEBUG
    }
