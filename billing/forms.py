from django import forms

from billing.models import StripeCustomer


class PaymentForm(forms.ModelForm):
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
    stripe_id = forms.CharField(
        required=True,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = StripeCustomer
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)
        for field in ['first_name', 'last_name', 'email']:
            self.fields[field].widget.attrs['class'] = 'form-control'
