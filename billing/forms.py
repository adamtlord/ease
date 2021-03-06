from django import forms
from django.core.exceptions import ValidationError

from billing.models import StripeCustomer, Plan, GroupMembership, Gift


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
    billing_zip = forms.CharField(
        required=True,
        label="Billing zip code for this card"
    )

    class Meta:
        model = StripeCustomer
        fields = ['first_name', 'last_name', 'email', 'last_4_digits', 'billing_zip']

    def __init__(self, *args, **kwargs):
        unrequire = kwargs.pop('unrequire', False)
        super(StripeCustomerForm, self).__init__(*args, **kwargs)
        for field in STRIPE_CUSTOMER_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'
        if unrequire:
            for field in self.Meta.fields:
                self.fields[field].required = False


class AddFundsForm(StripeCustomerForm):
    amount = forms.DecimalField(
        label="Amount",
        min_value=0,
        max_digits=6,
        decimal_places=2,
        required=True
    )

    class Meta(StripeCustomerForm):
        model = StripeCustomer
        fields = StripeCustomerForm.Meta.fields + ['amount']

    def __init__(self, *args, **kwargs):
        super(AddFundsForm, self).__init__(*args, **kwargs)
        for field in ['amount', 'first_name', 'last_name', 'email', 'last_4_digits', 'billing_zip']:
            self.fields[field].widget.attrs['class'] = 'form-control'


class PaymentForm(StripeCustomerForm):
    plan = forms.ChoiceField(
        required=True,
        choices=Plan.CHOICES,
        initial=Plan.DEFAULT,
        widget=forms.RadioSelect()
    )
    same_card_for_both = forms.ChoiceField(
        choices=(
            (1, 'Yes'),
            (0, 'No, I\'ll enter another card on the next page'),
            (2, 'No, please collect that billing information later'),
        ),
        widget=forms.RadioSelect(),
        label="Should we bill rides that are not included in your plan to this credit card too?"
    )
    billing_zip = forms.CharField(
        required=True,
        label="Billing zip code for this card"
    )
    coupon = forms.CharField(
        required=False,
        label="Do you have a coupon code?"
    )

    class Meta:
        model = StripeCustomer
        fields = ['first_name', 'last_name', 'email', 'last_4_digits', 'billing_zip']

    def __init__(self, *args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)
        for field in STRIPE_CUSTOMER_FIELDS + ['plan', 'coupon']:
            self.fields[field].widget.attrs['class'] = 'form-control'


class AdminPaymentForm(StripeCustomerForm):
    plan = forms.ChoiceField(
        required=True,
        choices=Plan.CHOICES,
        initial=Plan.DEFAULT
    )
    same_card_for_both = forms.ChoiceField(
        choices=(
            (1, 'Yes'),
            (0, 'No, enter another card on the next page'),
            (2, 'No, collect billing information later'),
        ),
        label="Bill rides not included in the plan to this credit card too?")
    billing_zip = forms.CharField(
        required=True,
        label="Billing zip code for this card"
    )
    coupon = forms.CharField(
        required=False,
        label="Do you have a coupon code?"
    )

    class Meta:
        model = StripeCustomer
        fields = ['first_name', 'last_name', 'email', 'last_4_digits', 'billing_zip']

    def __init__(self, *args, **kwargs):
        super(AdminPaymentForm, self).__init__(*args, **kwargs)
        for field in STRIPE_CUSTOMER_FIELDS + ['plan', 'same_card_for_both', 'coupon']:
            self.fields[field].widget.attrs['class'] = 'form-control'


class GiftForm(forms.ModelForm):
    relationship = forms.CharField(
        label="Your relationship to the primary rider",
        required=False
    )
    gift_date = forms.DateField(
        label="On what date will you present this gift? (optional)",
        help_text="We call every one of our new members, and don't want to ruin the surprise for you!",
        required=False
    )

    class Meta:
        model = Gift
        fields = ['first_name', 'last_name', 'relationship', 'gift_date']

    def __init__(self, *args, **kwargs):
        super(GiftForm, self).__init__(*args, **kwargs)
        for field in self.Meta.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class CSVUploadForm(forms.Form):
    file_upload = forms.FileField()

    # Excel on Windows may send through csv files. Just skip this check
    # with a strange content-type
    # https://github.com/thoughtbot/paperclip/issues/2170
    # https://stackoverflow.com/questions/7076042/what-mime-type-should-i-use-for-csv
    # def clean_file_upload(self):
    #     file_object = self.cleaned_data['file_upload']
    #     if file_object.content_type != 'text/csv':
    #         raise ValidationError(
    #             'Not a csv file?!',
    #             code='invalid')


class GroupMembershipFilterForm(forms.Form):
    INVOICE_STATUS_CHOICES = (
        (False, 'Not invoiced'),
        (True, 'Invoiced')
    )
    group = forms.ModelChoiceField(queryset=GroupMembership.objects.all(), required=False)
    start_date = forms.DateField(widget=forms.DateInput(), required=False)
    end_date = forms.DateField(widget=forms.DateInput(), required=False)
    invoiced = forms.ChoiceField(choices=INVOICE_STATUS_CHOICES, required=False, label="Invoice status")

    def __init__(self, *args, **kwargs):
        super(GroupMembershipFilterForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
