from django.utils import formats
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
    created_date = serializers.SerializerMethodField()
    invoiced_date = serializers.SerializerMethodField()
    paid_date = serializers.SerializerMethodField()

    def get_created_date(self, obj):
        if obj.created_date:
            return formats.date_format(obj.created_date, "SHORT_DATETIME_FORMAT")

    def get_invoiced_date(self, obj):
        if obj.invoiced_date:
            return formats.date_format(obj.invoiced_date, "SHORT_DATETIME_FORMAT")

    def get_paid_date(self, obj):
        if obj.paid_date:
            return formats.date_format(obj.paid_date, "SHORT_DATETIME_FORMAT")

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
