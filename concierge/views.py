from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory

from accounts.models import Customer
from concierge.forms import CustomerForm, DestinationForm, CreateHomeForm, UpdateHomeForm
from rides.models import Destination


@staff_member_required
def dashboard(request, template='concierge/dashboard.html'):
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
    d = {}
    d['customer'] = get_object_or_404(Customer, pk=pk)

    return render(request, template, d)


@staff_member_required
def customer_update(request, pk, template='concierge/customer_update.html'):

    customer = get_object_or_404(Customer, pk=pk)

    DestinationFormSet = inlineformset_factory(Customer,
                                               Destination,
                                               form=DestinationForm,
                                               can_delete=True)

    if request.method == "POST":
        form = CustomerForm(request.POST)
        home_form = UpdateHomeForm(request.POST, instance=customer.home)
        destination_formset = DestinationFormSet(request.POST, instance=customer, queryset=Destination.objects.exclude(home=True))

        if all([form.is_valid(), home_form.is_valid(), destination_formset.is_valid()]):
            form.save()
            home_form.save()
            destination_formset.save()

            messages.add_message(request, messages.SUCCESS, 'Customer {} successfully updated!'.format(customer))
            return redirect('customer_detail', customer.id)

    else:
        form = CustomerForm(instance=customer)
        home_form = UpdateHomeForm(instance=customer.home)
        destination_formset = DestinationFormSet(instance=customer, queryset=Destination.objects.exclude(home=True))

    d = {
        'form': form,
        'home_form': home_form,
        'destination_formset': destination_formset
    }

    return render(request, template, d)


@staff_member_required
def customer_delete(request, pk):
    messages.add_message(request, messages.SUCCESS, 'Deleted')
    return redirect(reverse('customer_list'))
