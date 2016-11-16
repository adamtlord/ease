from django import forms

from accounts.models import Customer
from rides.models import Destination

HOME_FIELDS = [
    'name',
    'street1',
    'street2',
    'city',
    'state',
    'zip_code'
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
