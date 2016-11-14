from django import forms

from rides.models import Destination

HOME_FIELDS = [
    'name',
    'street1',
    'street2',
    'city',
    'state',
    'zip_code',
]

DESTINATION_FIELDS = HOME_FIELDS + [
    'name',
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


class HomeForm(forms.ModelForm):
    street1 = forms.CharField(label="Address")

    class Meta:
        model = Destination
        fields = HOME_FIELDS

    def __init__(self, *args, **kwargs):
        super(HomeForm, self).__init__(*args, **kwargs)
        for field in HOME_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'
        for field in ['street1', 'city', 'state', 'zip_code']:
            self.fields[field].required = True
