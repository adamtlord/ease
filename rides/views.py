from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from accounts.models import Customer
from rides.models import Ride
from rides.forms import StartRideForm, DestinationForm, RideForm


def customer_rides(request, customer_id, template="concierge/customer_rides.html"):

    customer = get_object_or_404(Customer, pk=customer_id)
    rides_in_progress = Ride.in_progress.filter(customer=customer)
    completed_rides = Ride.objects.filter(customer=customer).exclude(id__in=rides_in_progress.values_list('id', flat=True))

    d = {
        'customer': customer,
        'rides_in_progress': rides_in_progress,
        'completed_rides': completed_rides,
        'ride_page': True
    }
    return render(request, template, d)


def ride_start(request, customer_id, template="rides/start_ride.html"):

    customer = get_object_or_404(Customer, pk=customer_id)

    if request.method == 'GET':

        start_ride_form = StartRideForm(customer=customer)
        add_starting_point_form = DestinationForm(prefix='add_start', initial={'customer': customer})
        add_destination_form = DestinationForm(prefix='add_dest', initial={'customer': customer})

    else:
        start_ride_form = StartRideForm(request.POST, customer=customer)
        add_starting_point_form = DestinationForm(request.POST, prefix='add_start')
        add_destination_form = DestinationForm(request.POST, prefix='add_dest')

        adding_destination = request.POST.get('add-destination', False)
        adding_start = request.POST.get('add-starting-point', False)

        if add_destination_form.is_valid() and add_starting_point_form.is_valid():

            new_ride = start_ride_form.save(commit=False)
            new_ride.customer = customer
            if adding_start:
                start = add_starting_point_form.save()
                new_ride.start = start
            if adding_destination:
                destination = add_destination_form.save()
                new_ride.destination = destination
            new_ride.start_date = timezone.now()
            new_ride.save()

            messages.success(request, "Ride started")
            return redirect('ride_edit', customer.id, new_ride.id)

    d = {
        'customer': customer,
        'start_ride_form': start_ride_form,
        'add_starting_point_form': add_starting_point_form,
        'add_destination_form': add_destination_form,
        'ride_page': True,
    }

    return render(request, template, d)


def ride_end(request, customer_id, ride_id):

    ride = get_object_or_404(Ride, pk=ride_id)

    ride.end_date = timezone.now()
    ride.save()
    messages.success(request, "Ride ended")

    return redirect('customer_detail', customer_id)


def ride_detail(request, customer_id, ride_id, template="concierge/ride_detail.html"):
    customer = get_object_or_404(Customer, pk=customer_id)
    ride = get_object_or_404(Ride, pk=ride_id)

    d = {
        'customer': customer,
        'ride': ride,
        'ride_page': True
    }

    return render(request, template, d)


def ride_edit(request, customer_id, ride_id, template="concierge/ride_edit.html"):
    customer = get_object_or_404(Customer, pk=customer_id)
    ride = get_object_or_404(Ride, pk=ride_id)

    if request.method == 'GET':

        form = RideForm(instance=ride)

    else:

        form = RideForm(request.POST, instance=ride)
        if form.is_valid():
            form.save()
            return redirect('ride_detail', customer.id, ride.id)
        else:
            print
            print form.errors
            print

    d = {
        'customer': customer,
        'ride': ride,
        'form': form,
        'ride_page': True
    }

    return render(request, template, d)
