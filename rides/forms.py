from django import forms

from accounts.models import CustomerProfile
from rides.models import Destination

DESTINATION_FIELDS = [
    'home',
    'nickname',
    'name',
    'street1',
    'street2',
    'city',
    'state',
    'zip_code',
    'country',
    'phone',
    'customer'
]


class DestinationForm(forms.ModelForm):
    home = forms.BooleanField(widget=forms.HiddenInput(), initial=False)

    class Meta:
        model = Destination
        fields = DESTINATION_FIELDS

    def __init__(self, *args, **kwargs):
        super(DestinationForm, self).__init__(*args, **kwargs)
        for field in DESTINATION_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'


class HomeForm(forms.ModelForm):
    home = forms.BooleanField(widget=forms.HiddenInput(), initial=True)
    nickname = forms.CharField(widget=forms.HiddenInput(), initial='Home')
    name = forms.CharField(widget=forms.HiddenInput(), initial='Home')
    customer = forms.ModelChoiceField(queryset=CustomerProfile.objects.all(), widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Destination
        fields = DESTINATION_FIELDS

    def __init__(self, *args, **kwargs):
        super(HomeForm, self).__init__(*args, **kwargs)
        for field in DESTINATION_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'
