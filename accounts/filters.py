import django_filters
from accounts.models import Customer


class CustomerFilter(django_filters.rest_framework.FilterSet):
    active = django_filters.BooleanFilter(name='user__is_active')

    class Meta:
        model = Customer
        fields = (
            'active',
            'first_name',
            'last_name',
            'email',
        )
