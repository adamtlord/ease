import pytz
from django.utils import formats
from rest_framework import serializers

from rides.models import Destination, Ride

from billing.serializers import InvoiceSerializer


class DestinationSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='destination-detail')

    class Meta:
        model = Destination
        fields = (
            'id',
            'name',
            'nickname',
            'fullname',
            'fulladdress',
            'street1',
            'street2',
            'unit',
            'city',
            'state',
            'zip_code',
            'country',
            'home',
            'latitude',
            'longitude',
            'timezone',
            'notes',
            'included_in_plan',
            'url'
        )


class RideSerializer(serializers.HyperlinkedModelSerializer):
    start = DestinationSerializer()
    customer = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    start = DestinationSerializer()
    destination = DestinationSerializer()
    invoice = InvoiceSerializer()

    def get_customer(self, obj):
        return dict(
            id=obj.customer.id,
            first_name=obj.customer.first_name,
            last_name=obj.customer.last_name,
        )

    def get_start_date(self, obj):
        # gotta represent the aware datetime as the correct local timezone
        # in a string, formatted correctly
        d = obj.start_date
        if obj.start and obj.start.timezone:
            d = obj.start_date.astimezone(pytz.timezone(obj.start.timezone))
        return formats.date_format(d, "SHORT_DATETIME_FORMAT")

    class Meta:
        model = Ride
        fields = (
            'cancelled',
            'cancelled_reason',
            'company',
            'complete',
            'cost',
            'customer',
            'destination',
            'distance',
            'id',
            'included_in_plan',
            'invoice',
            'rider',
            'start',
            'start_date',
            'total_cost',
            'total_fees',
        )
