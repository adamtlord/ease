from billing.models import Plan, GroupMembership
from rest_framework import viewsets
from billing.serializers import PlanSerializer, GroupMembershipSerializer


class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer


class GroupMembershipViewSet(viewsets.ModelViewSet):
    queryset = GroupMembership.objects.all()
    serializer_class = GroupMembershipSerializer
