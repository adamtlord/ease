from datetime import datetime

from django import forms
from django.core.exceptions import ValidationError

from accounts.models import Customer
from rides.models import Destination, Ride

HOME_FIELDS = [
    'name',
    'street1',
    'street2',
    'city',
    'state',
    'zip_code'
]

DESTINATION_FIELDS = HOME_FIELDS + [
    'nickname',
    'customer'
]

START_RIDE_FIELDS = [
    'start',
    'destination',
]

EDIT_RIDE_FIELDS = START_RIDE_FIELDS + [
    'customer',
    'start_date',
    'end_date',
    'cost',
    'distance',
    'service',
    'external_id',
    'notes'
]


class DestinationChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "{} - {}".format(obj.fullname, obj.fulladdress)


class DestinationForm(forms.ModelForm):
    customer = forms.ModelChoiceField(queryset=Customer.objects.all(), widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Destination
        fields = DESTINATION_FIELDS

    def __init__(self, *args, **kwargs):
        super(DestinationForm, self).__init__(*args, **kwargs)
        for field in ['name', 'street1', 'city', 'state', 'zip_code']:
            self.fields[field].required = True
        for field in DESTINATION_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'


class HomeForm(forms.ModelForm):
    street1 = forms.CharField(label="Address")
    residence_type = forms.ChoiceField(
        choices=Customer.RESIDENCE_TYPE_CHOICES,
        initial=Customer.SINGLE_FAMILY_HOME,
        required=False
        )
    residence_instructions = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        label="Anything we should know about this home pickup location?",
        help_text="For instance, is there a steep driveway and we should send the driver to the end of it? Is there a gate code?"
        )

    class Meta:
        model = Destination
        fields = HOME_FIELDS

    def __init__(self, *args, **kwargs):
        customer = kwargs.pop('customer', None)
        super(HomeForm, self).__init__(*args, **kwargs)
        for field in HOME_FIELDS + ['residence_type', 'residence_instructions']:
            self.fields[field].widget.attrs['class'] = 'form-control'
        for field in ['street1', 'city', 'state', 'zip_code']:
            self.fields[field].required = True
        if customer:
            self.fields['residence_type'].initial = customer.residence_type
            self.fields['residence_instructions'].initial = customer.residence_instructions


class StartRideForm(forms.ModelForm):
    start = DestinationChoiceField(
        queryset=Destination.objects.none(),
        empty_label=None,
        label="Pick up at",
        required=False
        )
    destination = DestinationChoiceField(
        queryset=Destination.objects.none(),
        empty_label=None,
        label="Destination",
        required=False
        )

    class Meta:
        model = Ride
        fields = START_RIDE_FIELDS

    def __init__(self, *args, **kwargs):
        customer = kwargs.pop('customer')
        super(StartRideForm, self).__init__(*args, **kwargs)
        self.fields['start'].queryset = Destination.objects.filter(customer=customer).order_by('-home')
        self.fields['destination'].queryset = Destination.objects.filter(customer=customer)
        for field in START_RIDE_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'
            self.fields[field].widget.attrs['style'] = 'width:100%;'


class RideForm(forms.ModelForm):
    start_date = forms.DateTimeField()
    end_date = forms.DateTimeField(required=False)
    customer = forms.ModelChoiceField(queryset=Customer.objects.all(), widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Ride
        fields = EDIT_RIDE_FIELDS

    def __init__(self, *args, **kwargs):
        super(RideForm, self).__init__(*args, **kwargs)
        self.fields['notes'].widget.attrs['rows'] = 4
        for field in EDIT_RIDE_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'
        for field in START_RIDE_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'
            self.fields[field].widget.attrs['style'] = 'width:100%;'
