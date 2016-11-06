from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory

from accounts.models import CustomerProfile
from accounts.forms import CustomerProfileForm
from rides.models import Destination
from rides.forms import DestinationForm, HomeForm


def customer_list(request, template='accounts/customerprofile_list.html'):
    d = {}
    d['customers'] = CustomerProfile.objects.all()

    return render(request, template, d)


def customer_create(request, template='accounts/customerprofile_create.html'):

    DestinationFormSet = inlineformset_factory(CustomerProfile, Destination, form=DestinationForm)

    if request.method == "POST":
        form = CustomerProfileForm(request.POST)
        if form.is_valid():
            new_customer = form.save()

            home_form = HomeForm(request.POST)
            if home_form.is_valid():
                home_address = home_form.save(commit=False)
                home_address.customer = new_customer
                home_address.save()

            destination_formset = DestinationFormSet(request.POST, instance=new_customer)
            if destination_formset.is_valid():
                destination_formset.save()

        return redirect('customer_detail', new_customer.id)

    else:
        form = CustomerProfileForm()
        home_form = HomeForm()
        destination_formset = DestinationFormSet()

    d = {
        'form': form,
        'home_form': home_form,
        'destination_formset': destination_formset
    }

    return render(request, template, d)


def customer_detail(request, pk, template='accounts/customerprofile_detail.html'):
    d = {}
    d['customer'] = get_object_or_404(CustomerProfile, pk=pk)

    return render(request, template, d)


def customer_update(request, pk, template='accounts/customerprofile_form.html'):
    d = {}
    d['customer'] = get_object_or_404(CustomerProfile, pk=pk)

    return render(request, template, d)


def customer_delete(request, pk):
    messages.add_message(request, messages.SUCCESS, 'Deleted')
    return redirect(reverse('customer_list'))
