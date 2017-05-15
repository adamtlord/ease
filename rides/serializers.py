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
    destination = DestinationSerializer()
    customer = serializers.HyperlinkedIdentityField(view_name='customer-detail')

    class Meta:
        model = Ride
        fields = (
            'start_date',
            'end_date',
            'request_time',
            'start',
            'destination',
            'cost',
            'fees',
            'fare_estimate',
            'distance',
            'company',
            'external_id',
            'complete',
            'invoice_item_id',
            'notes',
            'arrive_fee',
            'total_cost',
            'included_in_plan',
            'invoiced',
            'customer'
        )