from django import forms

from accounts.models import Customer, LovedOne, Rider
from concierge.models import Touch
from rides.models import Destination


CONTACT_FIELDS = [
    'first_name',
    'last_name',
    'email',
    'mobile_phone',
]

LOCATION_FIELDS = [
    # 'name',
    'street1',
    'street2',
    'city',
    'state',
    'zip_code',
    # 'country',
]

CUSTOMER_FIELDS = [
    'first_name',
    'last_name',
    'email',
    'known_as',
    'dob',
    'residence_type',
    'residence_instructions',
    'special_assistance',
    'notes',
    'home_phone',
    'mobile_phone',
    'preferred_phone',
    'send_updates',
]

TOUCH_FIELDS = [
    'customer',
    'date',
    'type',
    'notes',
]

UPDATE_HOME_FIELDS = [
    'street1',
    'street2',
    'city',
    'state',
    'zip_code',
]

CREATE_HOME_FIELDS = UPDATE_HOME_FIELDS + [
    'name',
]

DESTINATION_FIELDS = CREATE_HOME_FIELDS + [
    'nickname',
    'customer'
]

LOVED_ONE_FIELDS = CONTACT_FIELDS + LOCATION_FIELDS + [
    'relationship',
    'customer'
]

RIDER_FIELDS = [
    'first_name',
    'last_name',
    'mobile_phone',
    'customer'
]


class CustomerForm(forms.ModelForm):
    residence_instructions = forms.CharField(
        label="Anything we should know about this home pickup location?",
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )
    intro_call = forms.BooleanField(
        label="Intro call completed",
        required=False
    )

    class Meta:
        model = Customer
        fields = CUSTOMER_FIELDS + ['intro_call']

    def __init__(self, *args, **kwargs):
        super(CustomerForm, self).__init__(*args, **kwargs)
        for field in CUSTOMER_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'


class DestinationForm(forms.ModelForm):
    customer = forms.ModelChoiceField(queryset=Customer.objects.all(), widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Destination
        fields = DESTINATION_FIELDS + ['customer']

    def __init__(self, *args, **kwargs):
        super(DestinationForm, self).__init__(*args, **kwargs)
        for field in DESTINATION_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'


class CreateHomeForm(forms.ModelForm):
    name = forms.CharField(widget=forms.HiddenInput(), initial='Home')
    customer = forms.ModelChoiceField(queryset=Customer.objects.all(), widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Destination
        fields = CREATE_HOME_FIELDS

    def __init__(self, *args, **kwargs):
        super(CreateHomeForm, self).__init__(*args, **kwargs)
        for field in CREATE_HOME_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'


class UpdateHomeForm(forms.ModelForm):
    customer = forms.ModelChoiceField(queryset=Customer.objects.all(), widget=forms.HiddenInput())

    class Meta:
        model = Destination
        fields = UPDATE_HOME_FIELDS + ['customer']

    def __init__(self, *args, **kwargs):
        super(UpdateHomeForm, self).__init__(*args, **kwargs)
        for field in UPDATE_HOME_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'


class LovedOneForm(forms.ModelForm):

    class Meta:
        model = LovedOne
        fields = LOVED_ONE_FIELDS + ['receive_updates']

    def __init__(self, *args, **kwargs):
        super(LovedOneForm, self).__init__(*args, **kwargs)
        for field in LOVED_ONE_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'


class RiderForm(forms.ModelForm):
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    mobile_phone = forms.CharField(required=False)

    class Meta:
        model = Rider
        fields = RIDER_FIELDS

    def __init__(self, *args, **kwargs):
        super(RiderForm, self).__init__(*args, **kwargs)
        for field in RIDER_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Touch
        fields = TOUCH_FIELDS

    def __init__(self, *args, **kwargs):
        super(ActivityForm, self).__init__(*args, **kwargs)
        for field in TOUCH_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'
