from django.forms import ModelForm

from accounts.models import CustomerProfile

CUSTOMER_FIELDS = [
    'first_name',
    'last_name',
    'email',
    'known_as',
    'dob',
    'most_recent_ride',
    'spent_to_date',
    'residence_type',
    'residence_instructions',
    'special_assistance',
    'notes',
]


class CustomerProfileForm(ModelForm):
    class Meta:
        model = CustomerProfile
        fields = CUSTOMER_FIELDS

    def __init__(self, *args, **kwargs):
        super(CustomerProfileForm, self).__init__(*args, **kwargs)
        for field in CUSTOMER_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'
