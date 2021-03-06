from django import forms

from accounts.const import RESIDENCE_TYPE_CHOICES, SINGLE_FAMILY_HOME
from accounts.models import Customer, Rider, CustomUser
from rides.models import Destination, Ride, RideConfirmation


HOME_FIELDS = [
    'name',
    'street1',
    'street2',
    'unit',
    'city',
    'state',
    'zip_code',
    'notes',
    'address_for_gps',
]

DESTINATION_FIELDS = HOME_FIELDS + [
    'nickname',
]

START_RIDE_FIELDS = [
    'start',
    'destination',
    'start_date',
    'rider_link'
]

EDIT_RIDE_FIELDS = START_RIDE_FIELDS + [
    'customer',
    'start_date',
    'cost',
    'fare_estimate',
    'distance',
    'company',
    'external_id',
    'fees',
    'arrive_fee',
    'notes',
    'rider'
]

RIDER_FIELDS = [
    'first_name',
    'last_name',
    'mobile_phone',
    'customer',
    'notes'
]


class DestinationChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return u"{} - {}".format(obj.fullname, obj.fulladdress)


class DestinationForm(forms.ModelForm):
    customer = forms.ModelChoiceField(queryset=Customer.objects.all(), widget=forms.HiddenInput(), required=False)
    notes = forms.CharField(
        label="Anything we should know about this destination?",
        help_text="For instance, is there a steep driveway and we should send the driver to the end of it? Is there an entrance you prefer to use?",
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False
    )

    class Meta:
        model = Destination
        fields = DESTINATION_FIELDS + ['customer']

    def __init__(self, *args, **kwargs):
        super(DestinationForm, self).__init__(*args, **kwargs)
        for field in ['name', 'street1', 'city', 'state', 'zip_code']:
            self.fields[field].required = True
        for field in DESTINATION_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        dest = super(DestinationForm, self).save(commit=False)
        if self.has_changed():
            dest.set_ltlng()
        if commit:
            dest.save()
        return dest


class HomeForm(forms.ModelForm):
    street1 = forms.CharField(label="Address")
    residence_type = forms.ChoiceField(
        choices=RESIDENCE_TYPE_CHOICES,
        initial=SINGLE_FAMILY_HOME,
        required=False
    )
    notes = forms.CharField(
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
        for field in HOME_FIELDS + ['residence_type']:
            self.fields[field].widget.attrs['class'] = 'form-control'
        for field in ['street1', 'city', 'state', 'zip_code']:
            self.fields[field].required = True
        if customer:
            self.fields['residence_type'].initial = customer.residence_type

    def save(self, commit=True):
        home = super(HomeForm, self).save(commit=False)
        if self.has_changed():
            try:
                home.set_ltlng()
                home.set_timezone()
            except Customer.DoesNotExist:
                pass
        if commit:
            home.save()
        return home


class GroupAddressForm(HomeForm):
    street1 = forms.CharField(label="Physical Group Address")
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        label="Anything we should know about your location?",
        help_text="For instance, is there a steep driveway and we should send the driver to the end of it? Is there a gate code?"
    )


class StartRideForm(forms.ModelForm):
    start = DestinationChoiceField(
        queryset=Destination.objects.none(),
        empty_label=None,
        label="Pick up at",
        required=False
    )
    destination = DestinationChoiceField(
        queryset=Destination.objects.none(),
        empty_label=None,
        label="Destination",
        required=False
    )
    start_date = forms.DateTimeField(required=False)
    rider_link = forms.ModelChoiceField(
        label="Who is riding?",
        queryset=Rider.objects.none(),
        required=False
    )

    class Meta:
        model = Ride
        fields = START_RIDE_FIELDS

    def __init__(self, *args, **kwargs):
        customer = kwargs.pop('customer')
        super(StartRideForm, self).__init__(*args, **kwargs)
        self.fields['start'].queryset = Destination.objects.filter(customer=customer).order_by('-home')
        self.fields['destination'].queryset = Destination.objects.filter(customer=customer)
        self.fields['rider_link'].queryset = Rider.objects.filter(customer=customer).order_by('last_name', 'first_name')
        self.fields['rider_link'].empty_label = "{} (self)".format(customer.full_name)
        for field in START_RIDE_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'
            self.fields[field].widget.attrs['style'] = 'width:100%;'


class RideForm(forms.ModelForm):
    start_date = forms.DateTimeField()
    end_date = forms.DateTimeField(required=False)
    customer = forms.ModelChoiceField(queryset=Customer.objects.all(), widget=forms.HiddenInput(), required=False)
    complete = forms.BooleanField(required=False, label="Complete/Ready to Bill")
    start = DestinationChoiceField(
        queryset=Destination.objects.none(),
        empty_label=None,
        label="Pick up at"
    )
    destination = DestinationChoiceField(
        queryset=Destination.objects.none(),
        empty_label=None,
        label="Destination"
    )
    fees = forms.DecimalField(
        required=False,
        label="Additional fees",
        help_text="Use for cancellation fees or surcharges"
    )
    arrive_fee = forms.DecimalField(
        required=False,
        label="Dispatch fee"
    )
    rider_link = forms.ModelChoiceField(
        label="Who is riding?",
        queryset=Rider.objects.none(),
        required=False
    )

    class Meta:
        model = Ride
        fields = EDIT_RIDE_FIELDS + ['complete', 'included_in_plan']

    def __init__(self, *args, **kwargs):
        customer = kwargs.pop('customer')
        super(RideForm, self).__init__(*args, **kwargs)
        self.fields['start'].queryset = Destination.objects.filter(customer=customer).order_by('-home')
        self.fields['destination'].queryset = Destination.objects.filter(customer=customer)
        self.fields['notes'].widget.attrs['rows'] = 4
        self.fields['rider_link'].queryset = Rider.objects.filter(customer=customer).order_by('last_name', 'first_name')
        self.fields['rider_link'].empty_label = "{} (self)".format(customer.full_name)
        for field in EDIT_RIDE_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'
        for field in START_RIDE_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'
            self.fields[field].widget.attrs['style'] = 'width:100%;'


class CancelRideForm(forms.Form):
    ride_id = forms.IntegerField()
    next_url = forms.CharField()
    cancel_reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        label="Why are you deleting this ride?",
        help_text="(Do not delete this ride if you need to charge the customer a cancellation fee)"
    )


class ConfirmRideForm(forms.ModelForm):
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label="Confirmation notes",
    )
    confirmed_by = forms.ModelChoiceField(queryset=CustomUser.objects.filter(is_staff=True, is_active=True))

    class Meta:
        model = RideConfirmation
        fields = ('ride', 'confirmed_by', 'notes',)

    def __init__(self, *args, **kwargs):
        super(ConfirmRideForm, self).__init__(*args, **kwargs)
        self.fields['notes'].widget.attrs['class'] = 'form-control'
        self.fields['confirmed_by'].widget.attrs['class'] = 'form-control'


class AddRiderForm(forms.ModelForm):
    customer = forms.ModelChoiceField(queryset=Customer.objects.all(), widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Rider
        fields = RIDER_FIELDS

    def __init__(self, *args, **kwargs):
        super(AddRiderForm, self).__init__(*args, **kwargs)
        for field in RIDER_FIELDS:
            self.fields[field].widget.attrs['class'] = 'form-control'
        self.fields['notes'].widget.attrs['rows'] = 2


class RideExportForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(), required=False)
    end_date = forms.DateField(widget=forms.DateInput(), required=False)

