import pytz

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone, formats
from django.urls import reverse

from accounts.models import Customer
from common.utils import get_distance
from concierge.forms import DestinationForm
from rides.forms import StartRideForm, RideForm, CancelRideForm, ConfirmRideForm
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

    customer = get_object_or_404(Customer.objects.select_related('user').select_related('user__profile').prefetch_related('riders'), pk=customer_id)
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

            tz_abbrev = ''
            # immediate dispatch start_date comes in as UTC; scheduled start_date
            # comes in as tz of starting point
            if new_ride.start.timezone and new_ride.start_date.tzinfo != pytz.utc:
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
            if customer.plan and customer.plan.included_rides_per_month:
                if customer.included_rides_this_month < customer.plan.included_rides_per_month:
                    distance = new_ride.distance
                    if customer.plan.ride_distance_limit > 0 and distance < customer.plan.ride_distance_limit:
                        included = True
                    # (or)
                    if new_ride.start.home or new_ride.destination.home:
                        if new_ride.start.included_in_plan or new_ride.destination.included_in_plan:
                            included = True

            new_ride.included_in_plan = included

            # Figure out if this ride is outside regular hours and add a fee
            tz = pytz.timezone(settings.TIME_ZONE)
            concierge_start_time = new_ride.start_date.astimezone(tz)
            if not settings.ARRIVE_BUSINESS_HOURS[0] <= concierge_start_time.hour < settings.ARRIVE_BUSINESS_HOURS[1]:
                new_ride.fees = new_ride.fees or 0
                new_ride.fees += settings.ARRIVE_AFTER_HOURS_FEE

            if included:
                if new_ride.notes:
                    new_ride.notes += " "
                else:
                    new_ride.notes = ""
                new_ride.notes += "({} of {} included rides this cycle)".format(customer.included_rides_this_month + 1, customer.plan.included_rides_per_month)

            new_ride.added_by = request.user

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
    ride = get_object_or_404(Ride.objects.select_related('destination').select_related('start'), pk=ride_id)
    customer = get_object_or_404(Customer.objects.select_related('user').select_related('user__profile'), pk=ride.customer.id)

    cancel_form = CancelRideForm(initial={
        'ride_id': ride_id,
        'next_url': reverse('customer_detail', args=[customer.id])})

    confirmation_form = ConfirmRideForm(initial={
        'ride': ride,
        'confirmed_by': request.user
    })

    errors = {}

    if request.method == 'GET':
        form = RideForm(instance=ride, customer=customer)
    else:
        form = RideForm(request.POST, instance=ride, customer=customer)
        if form.is_valid():
            ride = form.save(commit=False)
            if ride.start.timezone:
                # get timezone object for customer
                start_tz = pytz.timezone(ride.start.timezone)
                # convert default (pac) datetime to naive
                naived_start_date = ride.start_date.replace(tzinfo=None)
                # re-localize datetime to customer's timezone
                localized_start_date = start_tz.localize(naived_start_date)
                # set start_date to re-localized datetime
                ride.start_date = localized_start_date
            ride.save()
            messages.success(request, "Ride saved successfully")
        else:
            errors = form.errors

    d = {
        'customer': customer,
        'ride': ride,
        'form': form,
        'cancel_form': cancel_form,
        'confirmation_form': confirmation_form,
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
        elif request.META['HTTP_REFERER']:
            return redirect(request.META['HTTP_REFERER'])
        return redirect('customer_detail', ride.customer.id)

    except Exception as ex:
        messages.error(request, ex.message)
        if next:
            return redirect(next)
        elif request.META['HTTP_REFERER']:
            return redirect(request.META['HTTP_REFERER'])
        return redirect('dashboard')


@staff_member_required
@require_POST
def ride_cancel(request):

    cancel_form = CancelRideForm(request.POST)

    if cancel_form.is_valid():
        next_url = cancel_form.cleaned_data['next_url']
        ride_id = cancel_form.cleaned_data['ride_id']
        try:
            ride = get_object_or_404(Ride, pk=ride_id)
            ride.cancelled = True
            ride.cancelled_reason = cancel_form.cleaned_data['cancel_reason']
            ride.cancelled_by = request.user
            ride.full_clean()
            ride.save()
            messages.success(request, "Ride cancelled and archived")
            if next_url:
                return redirect(next_url)
            elif request.META['HTTP_REFERER']:
                return redirect(request.META['HTTP_REFERER'])
            return redirect('customer_detail', ride.customer.id)

        except Exception as ex:
            messages.error(request, ex.message)
            if request.META['HTTP_REFERER']:
                return redirect(request.META['HTTP_REFERER'])
            return redirect('dashboard')


@staff_member_required
def ride_detail_modal(request, ride_id, template="rides/fragments/ride_detail_modal.html"):
    ride = get_object_or_404(Ride, pk=ride_id)
    d = {
        'ride': ride
    }
    return render(request, template, d)
