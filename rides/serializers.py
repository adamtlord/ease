from django.utils import formats
from rest_framework import serializers

from rides.models import Destination, Ride


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
    customer = serializers.CharField(source='customer.full_name')
    customer_id = serializers.CharField(source='customer.id')
    start_date = serializers.SerializerMethodField()
    start = DestinationSerializer()
    destination = DestinationSerializer()

    def get_start_date(self, obj):
        return formats.date_format(obj.start_date, "SHORT_DATETIME_FORMAT")

    class Meta:
        model = Ride
        fields = (
            'id',
            'complete',
            'customer',
            'customer_id',
            'rider',
            'start_date',
            'start',
            'destination',
            'distance',
            'included_in_plan'
        )
