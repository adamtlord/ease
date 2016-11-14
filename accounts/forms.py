from django import forms
from registration.forms import RegistrationForm
from accounts.const import TEXT_UPDATE_CHOICES
from accounts.models import CustomUser, UserProfile, Customer, Rider, LovedOne
from rides.models import Destination

CUSTOM_USER_FIELDS = [
    'email',
    'first_name',
    'last_name',
    'password1',
    'password2',
    'source',
    'source_other'
]

CUSTOMER_FIELDS = [
    'home_phone',
    'mobile_phone',
    'preferred_phone',
    'residence_instructions'
]

HOME_FIELDS = [
    'name',
    'street1',
    'street2',
    'city',
    'state',
    'zip_code',
]

RIDER_FIELDS = [
    'first_name',
    'last_name',
    'mobile_phone'
]

LOVEDONE_UPDATE_FIELDS = [
    'first_name',
    'last_name',
    'mobile_phone',
    'relationship'
]


class CustomUserRegistrationForm(RegistrationForm):
    first_name = forms.CharField(
        label="First name",
        required=True
    )
    last_name = forms.CharField(
        label="Last name",
        required=True
    )
    email = forms.EmailField(
        help_text='Will be used to log into the member account',
        required=True
    )
    password1 = forms.CharField(
        label="Create a password",
        strip=False,
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label="Please enter the password again",
        widget=forms.PasswordInput,
        strip=False,
        help_text=None,
    )
    source = forms.ChoiceField(
        label="How did you hear about Arrive?",
        choices=UserProfile.SOURCE_CHOICES,
        required=False
    )
    source_other = forms.CharField(
        label=None,
        max_length=255,
        required=False
    )

    def clean(self):
        super(RegistrationForm, self).clean()
        if self.cleaned_data.get('source') == UserProfile.OTHER:
            self.cleaned_data['source'] = self.cleaned_data['source_other']

    def save(self, request):
        user = super(RegistrationForm, self).save(request)
        # Store the common profile data.
        user.profile.source = self.cleaned_data['source']
        user.profile.save()
        return user

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super(CustomUserRegistrationForm, self).__init__(*args, **kwargs)
        for field in CUSTOM_USER_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs.pop('autofocus', None)
        self.fields['first_name'].widget.attrs['autofocus'] = 'autofocus'


class CustomerForm(forms.ModelForm):
    residence_instructions = forms.CharField(
        label="Anything we should know about this home pickup location?",
        help_text="For instance, is there a steep driveway and we should send the driver to the end of it? Is there a gate code?",
        widget=forms.Textarea,
        required=False
    )

    class Meta:
        model = Customer
        fields = CUSTOMER_FIELDS

    def __init__(self, *args, **kwargs):
        super(CustomerForm, self).__init__(*args, **kwargs)
        for field in CUSTOMER_FIELDS:
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


class RiderForm(forms.ModelForm):
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    mobile_phone = forms.CharField(required=False)

    class Meta:
        model = Rider
        fields = RIDER_FIELDS

    def __init__(self, *args, **kwargs):
        super(RiderForm, self).__init__(*args, **kwargs)
        for field in RIDER_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'


class CustomerPreferencesForm(forms.ModelForm):
    send_updates = forms.ChoiceField(
        label="Would you like to designate someone to receive your ride updates?",
        choices=TEXT_UPDATE_CHOICES,
        required=True)

    class Meta:
        model = Customer
        fields = ('send_updates',)

    def __init__(self, *args, **kwargs):
        super(CustomerPreferencesForm, self).__init__(*args, **kwargs)
        self.fields['send_updates'].widget.attrs['class'] = 'form-control'


class LovedOneForm(forms.ModelForm):
    mobile_phone = forms.CharField(label="Mobile phone number")

    class Meta:
        model = LovedOne
        fields = LOVEDONE_UPDATE_FIELDS

    def __init__(self, *args, **kwargs):
        super(LovedOneForm, self).__init__(*args, **kwargs)
        for field in LOVEDONE_UPDATE_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'
        for field in ['first_name', 'last_name', 'mobile_phone']:
            self.fields[field].required = True
