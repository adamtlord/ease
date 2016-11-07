from django import forms

from accounts.models import CustomerProfile
from rides.models import Destination

UPDATE_HOME_FIELDS = [
    'street1',
    'street2',
    'city',
    'state',
    'zip_code',
    'phone',
]

CREATE_HOME_FIELDS = UPDATE_HOME_FIELDS + [
    'name',
]

DESTINATION_FIELDS = CREATE_HOME_FIELDS + [
    'nickname',
    'customer'
]


class DestinationForm(forms.ModelForm):
    class Meta:
        model = Destination
        fields = DESTINATION_FIELDS

    def __init__(self, *args, **kwargs):
        super(DestinationForm, self).__init__(*args, **kwargs)
        for field in DESTINATION_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'


class CreateHomeForm(forms.ModelForm):
    name = forms.CharField(widget=forms.HiddenInput(), initial='Home')
    customer = forms.ModelChoiceField(queryset=CustomerProfile.objects.all(), widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Destination
        fields = CREATE_HOME_FIELDS

    def __init__(self, *args, **kwargs):
        super(CreateHomeForm, self).__init__(*args, **kwargs)
        for field in CREATE_HOME_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'


class UpdateHomeForm(forms.ModelForm):
    customer = forms.ModelChoiceField(queryset=CustomerProfile.objects.all(), widget=forms.HiddenInput())

    class Meta:
        model = Destination
        fields = UPDATE_HOME_FIELDS + ['customer']

    def __init__(self, *args, **kwargs):
        super(UpdateHomeForm, self).__init__(*args, **kwargs)
        for field in UPDATE_HOME_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'
