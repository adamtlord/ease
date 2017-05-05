from accounts.models import CustomUser, UserProfile, Customer
from rest_framework import viewsets
from accounts.serializers import UserSerializer, CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
