from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe

from accounts.models import CustomUser, Customer, LovedOne, Rider, UserProfile
from concierge.models import Touch
from rides.models import Destination
from registration.forms import RegistrationForm

CUSTOM_USER_FIELDS = [
    'email',
    'first_name',
    'last_name',
    'relationship',
    'password1',
    'password2',
    'source',
    'source_other',
    'phone'
]

CONTACT_FIELDS = [
    'first_name',
    'last_name',
    'email',
    'mobile_phone',
]

LOCATION_FIELDS = [
    # 'name',
    'street1',
    'street2',
    'city',
    'state',
    'zip_code',
    # 'country',
]

CUSTOMER_FIELDS = [
    'first_name',
    'last_name',
    'email',
    'known_as',
    'dob',
    'residence_type',
    'residence_instructions',
    'special_assistance',
    'notes',
    'home_phone',
    'mobile_phone',
    'preferred_phone'
]

TOUCH_FIELDS = [
    'customer',
    'date',
    'type',
    'notes',
    'type_other'
]

UPDATE_HOME_FIELDS = [
    'street1',
    'street2',
    'city',
    'state',
    'zip_code',
]

CREATE_HOME_FIELDS = UPDATE_HOME_FIELDS + [
    'name',
]

DESTINATION_FIELDS = CREATE_HOME_FIELDS + [
    'nickname',
    'notes'
]

LOVED_ONE_FIELDS = CONTACT_FIELDS + LOCATION_FIELDS + [
    'relationship',
    'customer'
]

RIDER_FIELDS = [
    'first_name',
    'last_name',
    'mobile_phone',
    'customer'
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
    relationship = forms.CharField(
        label="Relationship to the primary rider",
        required=False
    )
    password1 = forms.CharField(
        label="Create a password",
        strip=False,
        widget=forms.PasswordInput,
        help_text='Passwords must be at least 8 characters long'
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
        label="Please specify:",
        max_length=255,
        required=False
    )
    phone = forms.CharField(
        label="Phone number",
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
        user.profile.phone = self.cleaned_data['phone']
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


class AccountHolderForm(forms.ModelForm):
    first_name = forms.CharField(
        label="First name",
        required=True
    )
    last_name = forms.CharField(
        label="Last name",
        required=True
    )
    email = forms.EmailField(
        help_text='Used to log into the member account',
        required=True
    )
    relationship = forms.CharField(
        label="Relationship to the primary rider",
        required=False
    )
    phone = forms.CharField(
        label="Phone number",
        required=False
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'relationship')

    def __init__(self, *args, **kwargs):
        super(AccountHolderForm, self).__init__(*args, **kwargs)
        for field in ['email', 'first_name', 'last_name', 'relationship', 'phone']:
            self.fields[field].widget.attrs['class'] = 'form-control'


class CustomerForm(forms.ModelForm):
    residence_instructions = forms.CharField(
        label="Anything we should know about this home pickup location?",
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )
    intro_call = forms.BooleanField(
        label="Intro call completed",
        required=False
    )
    dob = forms.DateField(
        label="Date of birth",
        help_text="Please use the format MM/DD/YYYY",
        widget=forms.DateInput(format=('%m/%d/%Y'))
    )
    send_updates = forms.TypedChoiceField(
        coerce=lambda x: x == 'True',
        choices=((False, 'No'), (True, 'Yes')),
        initial=False,
        widget=forms.RadioSelect,
        required=False,
        label="Should we send the Primary Rider ride updates via text message?"
    )

    class Meta:
        model = Customer
        fields = CUSTOMER_FIELDS + ['intro_call', 'send_updates']

    def __init__(self, *args, **kwargs):
        super(CustomerForm, self).__init__(*args, **kwargs)
        for field in CUSTOMER_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'


class DestinationForm(forms.ModelForm):
    customer = forms.ModelChoiceField(queryset=Customer.objects.all(), widget=forms.HiddenInput(), required=False)
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5}),
        required=False
    )
    included_in_plan = forms.BooleanField(
        label="Always include rides to and from this destination in the customer's plan?",
        required=False
    )

    class Meta:
        model = Destination
        fields = DESTINATION_FIELDS + ['customer', 'included_in_plan']

    def __init__(self, *args, **kwargs):
        super(DestinationForm, self).__init__(*args, **kwargs)
        for field in DESTINATION_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'


class CreateHomeForm(forms.ModelForm):
    name = forms.CharField(widget=forms.HiddenInput(), initial='Home')
    customer = forms.ModelChoiceField(queryset=Customer.objects.all(), widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Destination
        fields = CREATE_HOME_FIELDS

    def __init__(self, *args, **kwargs):
        super(CreateHomeForm, self).__init__(*args, **kwargs)
        for field in CREATE_HOME_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'


class UpdateHomeForm(forms.ModelForm):
    customer = forms.ModelChoiceField(queryset=Customer.objects.all(), widget=forms.HiddenInput())

    class Meta:
        model = Destination
        fields = UPDATE_HOME_FIELDS + ['customer']

    def __init__(self, *args, **kwargs):
        super(UpdateHomeForm, self).__init__(*args, **kwargs)
        for field in UPDATE_HOME_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'


class LovedOneForm(forms.ModelForm):

    class Meta:
        model = LovedOne
        fields = LOVED_ONE_FIELDS + ['receive_updates']

    def __init__(self, *args, **kwargs):
        super(LovedOneForm, self).__init__(*args, **kwargs)
        for field in LOVED_ONE_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'


class RiderForm(forms.ModelForm):
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    mobile_phone = forms.CharField(required=False)
    customer = forms.ModelChoiceField(queryset=Customer.objects.all(), widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Rider
        fields = RIDER_FIELDS

    def __init__(self, *args, **kwargs):
        super(RiderForm, self).__init__(*args, **kwargs)
        for field in RIDER_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'


class ActivityForm(forms.ModelForm):
    type = forms.ChoiceField(
        label="Type",
        choices=Touch.TYPE_CHOICES,
        required=False
    )
    type_other = forms.CharField(
        label="Please specify:",
        max_length=255,
        required=False
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )
    date = forms.DateTimeField(
        label="Date and Time",
        required=False
    )

    def clean(self):
        super(ActivityForm, self).clean()
        if self.cleaned_data.get('type') == Touch.OTHER:
            self.cleaned_data['type'] = self.cleaned_data['type_other']

    class Meta:
        model = Touch
        fields = TOUCH_FIELDS

    def __init__(self, *args, **kwargs):
        super(ActivityForm, self).__init__(*args, **kwargs)
        for field in TOUCH_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'
