from rest_framework import serializers

from billing.models import Plan, GroupMembership


class PlanSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = Plan
        fields = '__all__'


class GroupMembershipSerializer(serializers.HyperlinkedModelSerializer):
    plan = serializers.HyperlinkedIdentityField(view_name='plan-detail')
    plan_id = serializers.IntegerField(source='id')

    class Meta:
        model = GroupMembership
        fields = (
            'name',
            'display_name',
            'plan_id',
            'plan',
            'active',
            'expiration_date',
            'includes_ride_cost',
            'includes_arrive_fee',
            'includes_subscription',
            'bill_online',
        )
