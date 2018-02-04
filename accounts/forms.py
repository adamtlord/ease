import pytz
from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe
from registration.forms import RegistrationForm
from accounts.const import TEXT_UPDATE_CHOICES
from accounts.models import CustomUser, UserProfile, Customer, Rider, LovedOne
from billing.models import GroupMembership


CUSTOM_USER_FIELDS = [
    'email',
    'first_name',
    'last_name',
]

CUSTOM_USER_REGISTRATION_FIELDS = CUSTOM_USER_FIELDS + [
    'relationship',
    'password1',
    'password2',
    'source',
    'source_other',
    'phone'
]

CUSTOMER_FIELDS = [
    'first_name',
    'last_name',
    'known_as',
    'dob',
    'email',
    'home_phone',
    'mobile_phone',
    'preferred_phone',
    'residence_instructions',
    'gift_date'
]

USER_PROFILE_FIELDS = [
    'user',
    'registration_complete',
    'on_behalf',
    'relationship',
    'receive_updates',
    'source',
    'phone',
    'timezone'
]

RIDER_FIELDS = [
    'first_name',
    'last_name',
    'mobile_phone'
]

LOVEDONE_NOTIFY_FIELDS = [
    'first_name',
    'last_name',
    'mobile_phone',
    'relationship'
]

LOVEDONE_USER_FIELDS = [
    'relationship',
    'mobile_phone',
    'receive_updates'
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
        label="Your relationship to the primary rider",
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
    accept_tos = forms.BooleanField(
        label=mark_safe('I have read and agree to the <a href="{}" target="_blank">Arrive Terms of Service</a>'.format(settings.TERMS_OF_SERVICE_URL)),
        required=True,
        error_messages={'required': 'You must accept the Terms of Service to use Arrive'},
    )
    phone = forms.CharField(
        required=False,
        label="Your phone number"
    )

    # def clean(self):
    #     super(RegistrationForm, self).clean()
    #     if self.cleaned_data.get('source') == UserProfile.OTHER:
    #         self.cleaned_data['source'] = self.cleaned_data['source_other']

    def save(self, request):
        user = super(RegistrationForm, self).save(request)
        # Store the common profile data.
        user.profile.source = self.cleaned_data['source']
        user.profile.source_specific = self.cleaned_data['source_other']
        user.profile.save()
        return user

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super(CustomUserRegistrationForm, self).__init__(*args, **kwargs)
        for field in CUSTOM_USER_REGISTRATION_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs.pop('autofocus', None)


class CustomUserForm(forms.ModelForm):
    email = forms.EmailField(
        required=False
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)
        for field in CUSTOM_USER_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'


class CustomUserProfileForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=CustomUser.objects.all(), widget=forms.HiddenInput())
    timezone = forms.ChoiceField(choices=[(x, x) for x in pytz.country_timezones['us']])

    class Meta:
        model = UserProfile
        fields = ['phone', 'timezone', 'user']

    def __init__(self, *args, **kwargs):
        super(CustomUserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class CustomerForm(forms.ModelForm):
    residence_instructions = forms.CharField(
        label="Anything we should know about this home pickup location?",
        help_text="For instance, is there a steep driveway and we should send the driver to the end of it? Is there a gate code?",
        widget=forms.Textarea(attrs={'rows': 5}),
        required=False
    )
    known_as = forms.CharField(required=False, help_text="Does your loved one go by something other than his or her first name?")
    dob = forms.DateField(
        label="Date of birth",
        help_text="Please use the format MM/DD/YYYY",
        widget=forms.DateInput(format=('%m/%d/%Y'))
    )
    gift_date = forms.DateField(
        label="If this is a gift, on what date will you present it?",
        help_text="We call every one of our new members, and don't want to ruin the surprise for you!",
        required=False
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
        fields = CUSTOMER_FIELDS + ['send_updates']

    def clean(self):
        cleaned_data = super(CustomerForm, self).clean()
        home_phone = cleaned_data.get('home_phone')
        mobile_phone = cleaned_data.get('mobile_phone')

        if not home_phone and not mobile_phone:
            msg = "Please include at least one phone number."
            self.add_error('home_phone', msg)
            self.add_error('mobile_phone', msg)
        if home_phone and not mobile_phone:
            cleaned_data['preferred_phone'] = 'h'
        if mobile_phone and not home_phone:
            cleaned_data['preferred_phone'] = 'm'

    def __init__(self, *args, **kwargs):
        is_self = kwargs.pop('is_self')
        super(CustomerForm, self).__init__(*args, **kwargs)
        for field in CUSTOMER_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'
        if is_self:
            self.fields['first_name'].required = False
            self.fields['last_name'].required = False
            self.fields['send_updates'].label = "Do you want to receive ride updates via text message?"


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
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    mobile_phone = forms.CharField(label="Mobile phone number", required=False)
    relationship = forms.CharField(required=False)

    class Meta:
        model = LovedOne
        fields = LOVEDONE_NOTIFY_FIELDS

    def __init__(self, *args, **kwargs):
        super(LovedOneForm, self).__init__(*args, **kwargs)
        for field in LOVEDONE_NOTIFY_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'


class LovedOnePreferencesForm(forms.ModelForm):
    relationship = forms.CharField(label="Your relationship to the primary customer", required=False)
    mobile_phone = forms.CharField(label="Your mobile phone number", required=False)
    receive_updates = forms.TypedChoiceField(
        coerce=lambda x: x == 'True',
        choices=((True, 'Yes'), (False, 'No')),
        widget=forms.RadioSelect,
        label="Would you like to receive ride updates?",
        required=False,
        # Not available through Lyft
        # required=True,
        help_text="We will only request this message be sent to you if the rider agrees to it.")

    class Meta:
        model = LovedOne
        fields = LOVEDONE_USER_FIELDS

    def __init__(self, *args, **kwargs):
        super(LovedOnePreferencesForm, self).__init__(*args, **kwargs)
        for field in ['relationship', 'mobile_phone']:
            self.fields[field].widget.attrs['class'] = 'form-control'


class GroupRegistrationForm(forms.ModelForm):
    name = forms.CharField(label="Group Name")
    phone = forms.CharField(label="Group Phone Number")
    default_user_address = forms.BooleanField(label="Should this address be the default home address for all riders?", required=False, initial=True)

    class Meta:
        model = GroupMembership
        fields = ('name', 'phone', 'default_user_address')

    def __init__(self, *args, **kwargs):
        super(GroupRegistrationForm, self).__init__(*args, **kwargs)
        for field in ['name', 'phone']:
            self.fields[field].widget.attrs['class'] = 'form-control'


class GroupContactRegistrationForm(CustomUserRegistrationForm):
    phone = forms.CharField(
        required=False,
        label="Primary Contact Phone Number"
    )
    email = forms.EmailField(
        label='Primary Group Contact Email',
        help_text='Receipts will be sent here',
        required=True
    )


class GroupCustomerForm(forms.ModelForm):
    known_as = forms.CharField(required=False, help_text="Does this person go by something other than his or her first name?")
    notes = forms.CharField(
        help_text="Does this customer have any special requirements or preferences we should know about?",
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )

    class Meta:
        model = Customer
        fields = ('first_name',
                  'last_name',
                  'known_as',
                  'mobile_phone',
                  'special_assistance',
                  'notes')

    def __init__(self, *args, **kwargs):
        super(GroupCustomerForm, self).__init__(*args, **kwargs)
        for field in self.Meta.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

