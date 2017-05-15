from rest_framework import viewsets

from accounts.filters import CustomerFilter
from accounts.models import CustomUser, Customer
from accounts.serializers import UserSerializer, CustomerSerializer
from common.paginators import DataTablesPagination


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()
    pagination_class = DataTablesPagination
    # filter_backends = (filters.DjangoFilterBackend,)
    # filter_fields = ('active', 'first_name',)
    filter_class = CustomerFilter


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
