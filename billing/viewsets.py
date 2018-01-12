from django_filters.rest_framework import DjangoFilterBackend
from billing.models import Plan, GroupMembership, Invoice
from rest_framework import viewsets
from billing.serializers import PlanSerializer, GroupMembershipSerializer, InvoiceSerializer


class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer


class GroupMembershipViewSet(viewsets.ModelViewSet):
    queryset = GroupMembership.objects.all()
    serializer_class = GroupMembershipSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('active',)


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
