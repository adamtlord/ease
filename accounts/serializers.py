from django.utils import formats

from accounts.models import CustomUser, Customer, Rider
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
    riders = RiderSerializer(many=True)
    group_membership = GroupMembershipSerializer()
    home = serializers.SerializerMethodField()
    rides = serializers.SerializerMethodField()
    last_ride_dt_u = serializers.SerializerMethodField()
    plan = serializers.SerializerMethodField()

    def get_home(self, obj):
        if obj.home:
            if obj.home.city and obj.home.state:
                return '{}, {}'.format(obj.home.city, obj.home.state)
            elif obj.home.state:
                return obj.home.state
        return ''

    def get_plan(self, obj):
        if obj.plan:
            return obj.plan.name
        else:
            return 'None'

    def get_rides(self, obj):
        return obj.ride_set.count()

    def get_last_ride_dt_u(self, obj):
        if obj.rides:
            return formats.date_format(obj.last_ride_dt, "U")

    class Meta:
        model = Customer
        fields = (
            'first_name',
            'last_name',
            'full_name',
            'age',
            'email',
            'mobile_phone',
            'dob',
            'group_membership',
            'gift_date',
            'home_phone',
            'home',
            'intro_call',
            'known_as',
            'last_ride_dt',
            'last_ride_dt_u',
            'notes',
            'plan',
            'preferred_phone',
            'phone_numbers_br',
            'residence_instructions',
            'residence_type',
            'rides',
            'preferred_service',
            'send_updates',
            'special_assistance',
            'timezone',
            'user',
            'riders'
        )
