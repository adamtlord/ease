from rest_framework import serializers

from billing.models import Plan, GroupMembership, Invoice


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


class InvoiceSerializer(serializers.HyperlinkedModelSerializer):
    customer_id = serializers.IntegerField()

    class Meta:
        model = Invoice
        fields = [
            'stripe_id',
            'customer_id',
            'created_date',
            'invoiced',
            'invoiced_date',
            'paid',
            'paid_date',
            'period_start',
            'period_end',
            'attempt_count',
            'total'
        ]
