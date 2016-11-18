from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.urlresolvers import reverse
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from accounts.models import Customer, LovedOne, Rider
from concierge.forms import CustomerForm, DestinationForm, CreateHomeForm, LovedOneForm, RiderForm
from rides.models import Destination
from rides.forms import HomeForm


def dashboard(request, template='concierge/dashboard.html'):
    if not request.user.is_authenticated:
        return redirect('concierge_login')

    if not request.user.is_staff:
        messages.add_message(request, messages.WARNING, 'Sorry, you\'re not allowed to go to the Concierge portal! Here\'s your profile:')
        return redirect('profile')

    d = {}

    return render(request, template, d)


@staff_member_required
def customer_list(request, template='concierge/customer_list.html'):
    d = {}
    d['customers'] = Customer.objects.all()

    return render(request, template, d)


@staff_member_required
def customer_create(request, template='concierge/customer_create.html'):

    DestinationFormSet = inlineformset_factory(Customer,
                                               Destination,
                                               form=DestinationForm,
                                               can_delete=False)

    if request.method == "POST":
        form = CustomerForm(request.POST)
        home_form = CreateHomeForm(request.POST)
        if form.is_valid() and home_form.is_valid():
            new_customer = form.save()
            home_address = home_form.save(commit=False)
            home_address.customer = new_customer
            home_address.home = True
            home_address.save()

            destination_formset = DestinationFormSet(request.POST,
                                                     instance=new_customer)
            if destination_formset.is_valid():
                destination_formset.save()

            messages.add_message(request, messages.SUCCESS, 'New customer {} created successfully!'.format(new_customer))
            return redirect('customer_detail', new_customer.id)

        else:
            destination_formset = DestinationFormSet(request.POST)

    else:
        form = CustomerForm()
        home_form = CreateHomeForm()
        destination_formset = DestinationFormSet()

    d = {
        'form': form,
        'home_form': home_form,
        'destination_formset': destination_formset
    }

    return render(request, template, d)


@staff_member_required
def customer_detail(request, pk, template='concierge/customer_detail.html'):

    customer = get_object_or_404(Customer, pk=pk)

    d = {
        'customer': customer,
        'riders': customer.rider_set.all()
    }

    return render(request, template, d)


@staff_member_required
def customer_update(request, pk, template='concierge/customer_update.html'):

    customer = get_object_or_404(Customer, pk=pk)
    home = customer.home
    DestinationFormSet = inlineformset_factory(Customer,
                                               Destination,
                                               form=DestinationForm,
                                               can_delete=True,
                                               extra=0)
    LovedOneFormSet = inlineformset_factory(Customer,
                                            LovedOne,
                                            form=LovedOneForm,
                                            can_delete=True,
                                            extra=0)
    RiderFormSet = inlineformset_factory(Customer,
                                         Rider,
                                         form=RiderForm,
                                         can_delete=True,
                                         extra=0)

    if request.method == "POST":
        customer_form = CustomerForm(request.POST, prefix='cust', instance=customer)
        home_form = HomeForm(request.POST, prefix='home', instance=home)
        destination_formset = DestinationFormSet(request.POST, instance=customer)
        lovedone_formset = LovedOneFormSet(request.POST, instance=customer)
        rider_formset = RiderFormSet(request.POST, instance=customer)

        if all([customer_form.is_valid(),
                home_form.is_valid(),
                destination_formset.is_valid(),
                lovedone_formset.is_valid(),
                rider_formset.is_valid()
                ]):
            customer_form.save()
            home_form.save()
            destination_formset.save()
            lovedone_formset.save(),
            rider_formset.save()

            messages.add_message(request, messages.SUCCESS, 'Customer {} successfully updated!'.format(customer))
            return redirect('customer_detail', customer.id)

    else:
        customer_form = CustomerForm(instance=customer, prefix='cust')
        home_form = HomeForm(instance=customer.home, prefix='home')
        destination_formset = DestinationFormSet(instance=customer, queryset=Destination.objects.exclude(home=True))
        lovedone_formset = LovedOneFormSet(instance=customer)
        rider_formset = RiderFormSet(instance=customer)

    d = {
        'customer': customer,
        'customer_form': customer_form,
        'home_form': home_form,
        'lovedone_formset': lovedone_formset,
        'rider_formset': rider_formset,
        'destination_formset': destination_formset
    }

    return render(request, template, d)


@staff_member_required
def customer_delete(request, pk):
    messages.add_message(request, messages.SUCCESS, 'Deleted')
    return redirect(reverse('customer_list'))


# AJAX VIEWS
def customer_search_data(request):
    customers = Customer.objects.all()
    customer_list = list()
    for customer in customers:
        customer_list.append({
            'name': customer.full_name,
            'home_phone': customer.home_phone,
            'mobile_phone': customer.mobile_phone,
            'id': customer.id,
            'tokens': [
                customer.first_name,
                customer.last_name,
                customer.home_phone,
                customer.mobile_phone
                ]
            })
    d = {
        'customers': customer_list
    }
    return JsonResponse(d)
