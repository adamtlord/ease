from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, get_object_or_404

from accounts.models import CustomerProfile


def customer_list(request, template='accounts/customerprofile_list.html'):
    d = {}
    d['customers'] = CustomerProfile.objects.all()

    return render(request, template, d)


def customer_create(request, template='accounts/customerprofile_create.html'):
    d = {}

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
