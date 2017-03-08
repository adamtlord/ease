import pytz
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone, formats
from accounts.models import Customer
from billing.utils import invoice_customer_rides
from common.utils import get_distance
from concierge.forms import DestinationForm
from rides.forms import StartRideForm, RideForm, CSVUploadForm
from rides.helpers import handle_lyft_upload, sort_rides_by_customer
from rides.models import Ride


@staff_member_required
def customer_rides(request, customer_id, template="concierge/customer_rides.html"):

    customer = get_object_or_404(Customer, pk=customer_id)
    rides = Ride.objects.filter(customer=customer)

    d = {
        'customer': customer,
        'rides': rides,
        'ride_page': True
    }
    return render(request, template, d)


@staff_member_required
def ride_start(request, customer_id, template="rides/start_ride.html"):

    customer = get_object_or_404(Customer, pk=customer_id)
    errors = []
    if request.method == 'GET':
        initial_start = None
        if customer.home:
            initial_start = customer.home
        initial_destination = None
        if customer.last_ride:
            if customer.last_ride.destination != customer.home:
                initial_start = customer.last_ride.destination
                initial_destination = customer.home
            else:
                initial_start = customer.home
                initial_destination = None

        start_ride_form = StartRideForm(
            customer=customer,
            initial={
                'start': initial_start,
                'destination': initial_destination
            }
        )
        add_starting_point_form = DestinationForm(prefix='add_start', initial={'customer': customer})
        add_destination_form = DestinationForm(prefix='add_dest', initial={'customer': customer})

    else:
        initial_start = None
        start_ride_form = StartRideForm(request.POST, customer=customer)
        add_starting_point_form = DestinationForm(request.POST, prefix='add_start')
        add_destination_form = DestinationForm(request.POST, prefix='add_dest')

        adding_start = request.POST.get('add-starting-point', False)
        adding_destination = request.POST.get('add-destination', False)

        valid_add_start = add_starting_point_form.is_valid() if adding_start else True
        valid_add_destination = add_destination_form.is_valid() if adding_destination else True

        if start_ride_form.is_valid() and valid_add_start and valid_add_destination:
            new_ride = start_ride_form.save(commit=False)
            new_ride.customer = customer
            if adding_start:
                start = add_starting_point_form.save()
                new_ride.start = start
            if adding_destination:
                destination = add_destination_form.save()
                new_ride.destination = destination

            if not start_ride_form.cleaned_data['start_date']:
                new_ride.start_date = timezone.now()

            if request.POST.get('schedule', None):
                tz_abbrev = ''
                if new_ride.start.timezone:
                    # get timezone object for customer
                    start_tz = pytz.timezone(new_ride.start.timezone)
                    # convert default (pac) datetime to naive
                    naived_start_date = new_ride.start_date.replace(tzinfo=None)
                    # re-localize datetime to customer's timezone
                    localized_start_date = start_tz.localize(naived_start_date)
                    tz_abbrev = localized_start_date.tzname()
                    # set start_date to re-localized datetime
                    new_ride.start_date = localized_start_date

            new_ride.distance = get_distance(new_ride)
            new_ride.save()

            # Figure out if this ride is included in the customer's plan
            included = False
            if customer.plan.included_rides_per_month:
                if customer.included_rides_this_month < customer.plan.included_rides_per_month:
                    distance = new_ride.distance
                    if customer.plan.ride_distance_limit > 0 and distance < customer.plan.ride_distance_limit:
                        included = True
                # (or)
                if new_ride.start.home or new_ride.destination.home:
                    if new_ride.start.included_in_plan or new_ride.destination.included_in_plan:
                        included = True

            new_ride.included_in_plan = included
            new_ride.save()

            if request.POST.get('schedule', None):

                messages.success(request, "Ride scheduled for {} {}".format(formats.date_format(new_ride.start_date, "SHORT_DATETIME_FORMAT"), tz_abbrev))
                return redirect('customer_history', customer.id)

            messages.success(request, "Ride started")
            return redirect('ride_edit', new_ride.id)

        else:
            if not valid_add_start:
                errors.append('start')
            if not valid_add_destination:
                errors.append('destination')
    d = {
        'customer': customer,
        'start_ride_form': start_ride_form,
        'add_starting_point_form': add_starting_point_form,
        'add_destination_form': add_destination_form,
        'ride_page': True,
        'geolocate': initial_start,
        'errors': errors
    }

    return render(request, template, d)


@staff_member_required
def ride_end(request, ride_id):

    ride = get_object_or_404(Ride, pk=ride_id)

    ride.end_date = timezone.now()
    ride.complete = True
    ride.save()
    messages.success(request, "Ride ended")

    return redirect('customer_detail', ride.customer.id)


@staff_member_required
def ride_detail(request, customer_id, ride_id, template="concierge/ride_detail.html"):
    customer = get_object_or_404(Customer, pk=customer_id)
    ride = get_object_or_404(Ride, pk=ride_id)

    d = {
        'customer': customer,
        'ride': ride,
        'ride_page': True
    }

    return render(request, template, d)


@staff_member_required
def ride_edit(request, ride_id, template="concierge/ride_edit.html"):
    ride = get_object_or_404(Ride, pk=ride_id)
    customer = get_object_or_404(Customer, pk=ride.customer.id)
    errors = {}
    if request.method == 'GET':
        form = RideForm(instance=ride, customer=customer)
    else:
        form = RideForm(request.POST, instance=ride, customer=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Ride saved successfully")
        else:
            errors = form.errors

    d = {
        'customer': customer,
        'ride': ride,
        'form': form,
        'ride_page': True,
        'errors': errors
    }

    return render(request, template, d)


@staff_member_required
def ride_delete(request, ride_id):

    next = request.GET.get('next', None)
    try:
        ride = get_object_or_404(Ride, pk=ride_id)
        ride.delete()
        messages.success(request, "Ride cancelled and deleted")
        if next:
            return redirect(next)
        return redirect('customer_detail', ride.customer.id)

    except Exception as ex:
        messages.error(request, ex.message)
        if next:
            return redirect(next)
        return redirect('dashboard')


@staff_member_required
def rides_ready_to_bill(request, template="rides/ready_to_bill.html"):

    rides = Ride.ready_to_bill.all().order_by('-start_date')
    customers = sort_rides_by_customer(rides)

    success_included = []
    success_billed = []
    success_total = 0
    errors = []
    total = 0

    if request.method == 'POST':

        idlist = request.POST.getlist('ride')
        rides_to_bill = Ride.objects.filter(id__in=idlist)
        sorted_rides = sort_rides_by_customer(rides_to_bill)

        for customer, rides in sorted_rides.items():
            response = invoice_customer_rides(customer, rides)
            success_included += response['success_included']
            success_billed += response['success_billed']
            success_total += response['success_total']
            errors += response['errors']
            total += response['total']

        rides = Ride.ready_to_bill.all()
        customers = sort_rides_by_customer(rides)

    d = {
        'ready_page': True,
        'customers': customers,
        'success_included': success_included,
        'success_billed': success_billed,
        'success_total': success_total,
        'errors': errors,
        'total': total
    }

    return render(request, template, d)


@staff_member_required
def rides_incomplete(request, template="rides/incomplete.html"):

    rides = Ride.objects.filter(Q(complete=False) | Q(cost__isnull=True)).order_by('-start_date')
    customers = sort_rides_by_customer(rides)

    d = {
        'incomplete_page': True,
        'customers': customers
    }
    return render(request, template, d)


@staff_member_required
def rides_invoiced(request, template="rides/invoiced.html"):
    rides = Ride.objects.filter(invoice__isnull=False).order_by('-start_date')

    d = {
        'invoiced_page': True,
        'rides': rides
    }
    return render(request, template, d)


@staff_member_required
def rides_upload(request, template="rides/upload.html"):

    results = {}

    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)

        if form.is_valid():
            upload = request.FILES['file_upload']
            if upload:
                results = handle_lyft_upload(request.FILES['file_upload'])
            else:
                messages.error(request, "No file!")

    else:
        form = CSVUploadForm()

    d = {
        'upload_page': True,
        'form': form,
        'results': results,
    }
    return render(request, template, d)


@staff_member_required
def ride_detail_modal(request, ride_id, template="rides/fragments/ride_detail_modal.html"):
    ride = get_object_or_404(Ride, pk=ride_id)
    d = {
        'ride': ride
    }
    return render(request, template, d)
