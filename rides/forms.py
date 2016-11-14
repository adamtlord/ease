from django import forms

from rides.models import Destination

HOME_FIELDS = [
    'street1',
    'street2',
    'city',
    'state',
    'zip_code',
]

DESTINATION_FIELDS = HOME_FIELDS + [
    'name',
    'nickname'
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
    class Meta:
        model = Destination
        fields = HOME_FIELDS

    def __init__(self, *args, **kwargs):
        super(HomeForm, self).__init__(*args, **kwargs)
        for field in HOME_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'
