from accounts.models import CustomUser, UserProfile, Customer, Rider
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    on_behalf = serializers.BooleanField(source='profile.on_behalf')
    relationship = serializers.CharField(source='profile.relationship')
    source = serializers.CharField(source='profile.source')
    phone = serializers.CharField(source='profile.phone')
    timezone = serializers.CharField(source='profile.timezone')
    url = serializers.HyperlinkedIdentityField(view_name='customuser-detail')

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
            'url'
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
            'send_updates'
        )


class CustomerSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerializer()
    riders = RiderSerializer(many=True)

    class Meta:
        model = Customer
        fields = (
            'first_name',
            'last_name',
            'email',
            'mobile_phone',
            'dob',
            # 'group_membership',
            'gift_date',
            'home_phone',
            'intro_call',
            'known_as',
            # 'last_ride',
            'notes',
            # 'plan',
            'preferred_phone',
            'residence_instructions',
            'residence_type',
            # 'ride_account',
            'preferred_service',
            'send_updates',
            'special_assistance',
            'spent_to_date',
            # 'subscription_account',
            'timezone',
            'user',
            'riders'
        )
