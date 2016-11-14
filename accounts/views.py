from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.forms import inlineformset_factory
# from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
# from django.forms import inlineformset_factory

from common.decorators import anonymous_required
from accounts.models import Customer, LovedOne
from accounts.forms import CustomUserRegistrationForm, CustomerForm, HomeForm, RiderForm, CustomerPreferencesForm, LovedOneForm
from rides.models import Destination
from rides.forms import DestinationForm, HomeForm


@anonymous_required
def register_self(request, template='accounts/register.html'):
    if not settings.REGISTRATION_OPEN:
        messages.info(request, "Registration is temporarily closed. We are sorry for the inconvenience.")
        return redirect('homepage')

    if request.method == 'GET':
        register_form = CustomUserRegistrationForm(prefix='reg')
        customer_form = CustomerForm(prefix='cust')
        home_form = HomeForm(prefix='home')
        rider_form = RiderForm(prefix='rider')
    else:
        register_form = CustomUserRegistrationForm(request.POST, prefix='reg')
        customer_form = CustomerForm(request.POST, prefix='cust')
        home_form = HomeForm(request.POST, prefix='home')
        rider_form = RiderForm(request.POST, prefix='rider')

        if all([
                register_form.is_valid(),
                customer_form.is_valid(),
                home_form.is_valid(),
                rider_form.is_valid()]):
            # save user
            new_user = register_form.save(request)
            # populate and save customer
            new_customer = customer_form.save(commit=False)
            new_customer.user = new_user
            new_customer.first_name = new_user.first_name
            new_customer.last_name = new_user.last_name
            new_customer.email = new_user.email
            new_customer.save()
            # populate and save home address
            home_address = home_form.save(commit=False)
            home_address.name = 'Home'
            home_address.customer = new_customer
            home_address.home = True
            home_address.save()
            # populate and save rider info
            rider = rider_form.save(commit=False)
            rider.customer = new_customer
            rider.save()

            authenticated_user = auth.authenticate(username=new_user.get_username(), password=register_form.cleaned_data['password1'])
            authenticated_user.backend = settings.AUTHENTICATION_BACKENDS[0]
            auth.login(request, authenticated_user)

            return redirect('profile')

    d = {
        'self': True,
        'lovedone': False,
        'register_form': register_form,
        'customer_form': customer_form,
        'home_form': home_form,
        'rider_form': rider_form
        }
    return render(request, template, d)


@login_required
def register_self_preferences(request, template='accounts/register_preferences.html'):

    customer = request.user.get_customer()

    LovedOneFormset = inlineformset_factory(Customer,
                                            LovedOne,
                                            form=LovedOneForm,
                                            can_delete=False,
                                            extra=1)

    if request.method == 'GET':
        preferences_form = CustomerPreferencesForm(instance=customer)
        lovedone_formset = LovedOneFormset(instance=customer)
    else:
        preferences_form = CustomerPreferencesForm(request.POST, instance=customer)
        lovedone_formset = LovedOneFormset(request.POST, instance=customer)

        if preferences_form.is_valid() and lovedone_formset.is_valid():
            preferences_form.save()
            lovedone_formset.save()

            return redirect('profile')

    d = {
        'self': True,
        'lovedone': False,
        'preferences_form': preferences_form,
        'lovedone_formset': lovedone_formset
    }
    return render(request, template, d)


@login_required
def register_self_destinations(request, template='accounts/register_destinations.html'):

    customer = request.user.get_customer()
    home = customer.destination_set.filter(home=True).first()

    DestinationFormset = inlineformset_factory(Customer,
                                               Destination,
                                               form=DestinationForm,
                                               can_delete=False)

    if request.method == 'GET':
        destination_formset = DestinationFormset(instance=customer, queryset=Destination.objects.exclude(home=True))
        home_form = HomeForm(instance=home)
    else:

        destination_formset = DestinationFormset(request.POST, instance=customer)
        home_form = HomeForm(request.POST, instance=home)

        if home_form.is_valid() and destination_formset.is_valid():

            home_form.save()
            destination_formset.save()

            return redirect('profile')

    d = {
        'self': True,
        'lovedone': False,
        'destination_formset': destination_formset,
        'home_form': home_form
    }
    return render(request, template, d)


@anonymous_required
def register_lovedone(request, template='accounts/register.html'):
    if not settings.REGISTRATION_OPEN:
        messages.info(request, "Registration is temporarily closed. We are sorry for the inconvenience.")
        return redirect('homepage')

    if request.method == 'GET':
        register_form = CustomUserRegistrationForm()
    else:
        register_form = CustomUserRegistrationForm(request.POST)

        if register_form.is_valid():
            new_user = register_form.save()

            authenticated_user = auth.authenticate(username=new_user.get_username(), password=register_form.cleaned_data['password1'])
            authenticated_user.backend = settings.AUTHENTICATION_BACKENDS[0]
            auth.login(request, authenticated_user)

            return redirect('profile')

    d = {
        'self': False,
        'lovedone': True,
        'register_form': register_form
        }
    return render(request, template, d)


@login_required
def profile(request, template='accounts/profile.html'):

    return render(request, template)
