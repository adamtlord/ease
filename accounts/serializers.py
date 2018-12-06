from django.utils.timesince import timesince

from accounts.models import CustomUser, Customer, Rider
from rides.serializers import DestinationSerializer
from billing.serializers import GroupMembershipSerializer, PlanSerializer

from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    on_behalf = serializers.BooleanField(source='profile.on_behalf')
    relationship = serializers.CharField(source='profile.relationship')
    source = serializers.CharField(source='profile.source')
    phone = serializers.CharField(source='profile.phone')
    timezone = serializers.CharField(source='profile.timezone')

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'date_joined',
            'on_behalf',
            'relationship',
            'source',
            'phone',
            'timezone',
        )


class RiderSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Rider
        fields = (
            'first_name',
            'last_name',
            'email',
            'mobile_phone',
            'relationship',
            'send_updates',
        )


class CustomerSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerializer()
    # riders = RiderSerializer(many=True)
    # group_membership = GroupMembershipSerializer()
    home = DestinationSerializer()
    ride_count = serializers.SerializerMethodField()
    plan = PlanSerializer()
    last_ride = serializers.SerializerMethodField()
    serializers.DateTimeField(source='last_ride.start_date')

    def get_last_ride(self, obj):
        if obj.last_ride_at:
            return u'{} ago'.format(timesince(obj.last_ride_at))
        return ''

    def get_ride_count(self, obj):
        return obj.ride_count

    class Meta:
        model = Customer
        fields = (
            'age',
            'dob',
            'email',
            'full_name',
            # 'group_membership',
            'home',
            'home_phone',
            'id',
            'is_active',
            'known_as',
            'last_ride',
            'mobile_phone',
            'notes',
            'phone_numbers_br',
            'plan',
            'preferred_phone',
            'preferred_service',
            'residence_instructions',
            'residence_type',
            'ride_count',
            # 'riders',
            # 'send_updates',
            'special_assistance',
            'timezone',
            'user'
        )
