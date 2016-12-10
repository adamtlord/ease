from django import forms


from billing.models import StripeCustomer, Plan


STRIPE_CUSTOMER_FIELDS = [
    'first_name',
    'last_name',
    'email',
    'billing_zip'
]


class StripeCustomerForm(forms.ModelForm):
    first_name = forms.CharField(
        label="First name",
        required=True
    )
    last_name = forms.CharField(
        label="Last name",
        required=True
    )
    email = forms.EmailField(
        required=True
    )
    last_4_digits = forms.CharField(
        required=True,
        min_length=4,
        max_length=4,
        widget=forms.HiddenInput()
    )
    stripe_token = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = StripeCustomer
        fields = ['first_name', 'last_name', 'email', 'last_4_digits', 'billing_zip']

    def __init__(self, *args, **kwargs):
        super(StripeCustomerForm, self).__init__(*args, **kwargs)
        for field in STRIPE_CUSTOMER_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'


class PaymentForm(StripeCustomerForm):
    plan = forms.ChoiceField(
        required=True,
        choices=Plan.CHOICES,
        widget=forms.RadioSelect()
    )
    same_card_for_both = forms.ChoiceField(
        choices=(
            (1, 'Yes'),
            (0, 'No, I\'ll enter another card on the next page'),
            (2, 'No, please collect billing information from the member later'),
        ),
        widget=forms.RadioSelect(),
        label="Should we bill rides that are not included in your plan to this credit card too?"
    )
    billing_zip = forms.CharField(
        required=True,
        label="Billing zip code for this card"
    )

    class Meta:
        model = StripeCustomer
        fields = ['first_name', 'last_name', 'email', 'last_4_digits', 'billing_zip']

    def __init__(self, *args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)
        for field in STRIPE_CUSTOMER_FIELDS + ['plan']:
            self.fields[field].widget.attrs['class'] = 'form-control'
