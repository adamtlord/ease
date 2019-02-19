import pytz
import csv

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone, formats
from django.urls import reverse

from accounts.models import Customer
from accounts.helpers import convert_date
from common.utils import get_distance
from concierge.forms import DestinationForm
from rides.forms import StartRideForm, RideForm, CancelRideForm, AddRiderForm, \
    ConfirmRideForm, RideExportForm
from rides.models import Ride


@staff_member_required
def customer_rides(request, customer_id, template="concierge/customer_rides.html"):

    customer = get_object_or_404(Customer, pk=customer_id)
    rides = Ride.objects.filter(customer=customer).prefetch_related('customer').prefetch_related('customer__plan')

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
        add_rider_form = AddRiderForm(prefix='add_rider', initial={'customer': customer})

    else:
        initial_start = None
        start_ride_form = StartRideForm(request.POST, customer=customer)
        add_starting_point_form = DestinationForm(request.POST, prefix='add_start')
        add_destination_form = DestinationForm(request.POST, prefix='add_dest')
        add_rider_form = AddRiderForm(request.POST, prefix='add_rider')

        adding_start = request.POST.get('add-starting-point', False)
        adding_destination = request.POST.get('add-destination', False)
        adding_rider = request.POST.get('add-rider', False)

        valid_add_start = add_starting_point_form.is_valid() if adding_start else True
        valid_add_destination = add_destination_form.is_valid() if adding_destination else True
        valid_add_rider = add_rider_form.is_valid() if adding_rider else True

        if start_ride_form.is_valid() and valid_add_start and valid_add_destination and valid_add_rider:
            new_ride = start_ride_form.save(commit=False)
            new_ride.customer = customer
            if adding_start:
                start = add_starting_point_form.save()
                new_ride.start = start
            if adding_destination:
                destination = add_destination_form.save()
                new_ride.destination = destination
            if adding_rider:
                rider_link = add_rider_form.save()
                new_ride.rider_link = rider_link

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

            # Add Arrive dispatch fee
            new_ride.arrive_fee = new_ride.get_arrive_fee
            # Figure out if this ride is outside regular hours and add a fee
            if customer.plan.after_hours_fee:
                tz = pytz.timezone(settings.TIME_ZONE)
                concierge_start_time = new_ride.start_date.astimezone(tz)

                business_hours = settings.ARRIVE_WEEKDAY_BUSINESS_HOURS
                if concierge_start_time.weekday() in [5, 6]:
                    business_hours = settings.ARRIVE_WEEKEND_BUSINESS_HOURS

                morning_cutoff = concierge_start_time.replace(hour=business_hours[0], minute=0, second=0, microsecond=0)
                evening_cutoff = concierge_start_time.replace(hour=business_hours[1], minute=1, second=0, microsecond=0)
                if not morning_cutoff < concierge_start_time < evening_cutoff:
                    new_ride.arrive_fee = new_ride.arrive_fee or 0
                    new_ride.arrive_fee += customer.plan.after_hours_fee

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
            if not valid_add_rider:
                errors.append('rider_link')

    d = {
        'customer': customer,
        'start_ride_form': start_ride_form,
        'add_starting_point_form': add_starting_point_form,
        'add_destination_form': add_destination_form,
        'add_rider_form': add_rider_form,
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
        'next_url': reverse('customer_detail', args=[customer.id])
    })

    errors = {}

    if request.method == 'GET':
        form = RideForm(instance=ride, customer=customer)
        confirmation_form = ConfirmRideForm(
            initial={
                'ride': ride,
                'confirmed_by': request.user,
            },
            prefix='conf'
        )
    else:
        form = RideForm(request.POST, instance=ride, customer=customer)
        confirmation_form = ConfirmRideForm(request.POST, prefix='conf')
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
            if 'is_confirmed' in request.POST and confirmation_form.is_valid():
                confirmation_form.save()
                messages.success(request, "Ride confirmed")
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


@staff_member_required
def ride_confirm_modal(request, ride_id, template="rides/fragments/ride_confirm_modal.html"):

    ride = get_object_or_404(Ride, pk=ride_id)

    if request.method == 'GET':
        form = ConfirmRideForm(
            initial={
                'ride': ride,
                'confirmed_by': request.user,
            },
        )

    else:
        form = ConfirmRideForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('upcoming_rides')
    d = {
        'ride': ride,
        'form': form
    }

    return render(request, template, d)


def ride_report(request, template="rides/ride_report.html"):

    if request.method == 'POST':
        search_form = RideExportForm(request.POST)
        try:
            tz = pytz.timezone(request.user.profile.timezone)
        except:
            tz = settings.TIME_ZONE

        start_date = pytz.utc.localize(convert_date(request.POST.get('start_date')))
        end_date = pytz.utc.localize(convert_date(request.POST.get('end_date')))

        rides = Ride.objects.filter(start_date__range=(start_date, end_date)) \
            .filter(complete=True) \
            .select_related('customer', 'invoice')

        response = HttpResponse(content_type='text/csv')
        filename = 'Ride Report {} - {}.csv'.format(request.POST.get('start_date'), request.POST.get('end'))
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)

        writer = csv.writer(response)
        writer.writerow([
            'Date/time',
            'Ride ID',
            'Company',
            'Cost',
            'Dispatch fee',
            'Additional fees',
            'Cost to customer',
            'Customer name',
            'Notes',
            'Invoice ID',
            'Cancelled'
        ])

        for ride in rides:
            notes = ''
            invoice = ''

            if ride.notes:
                notes = ride.notes.encode('utf-8')
            if ride.invoice:
                invoice = ride.invoice.stripe_id
            writer.writerow([
                            formats.date_format(ride.start_date.astimezone(tz), 'SHORT_DATETIME_FORMAT'),
                            ride.id,
                            ride.company,
                            '{0:.2f}'.format(ride.cost if ride.cost else 0),
                            '{0:.2f}'.format(ride.arrive_fee if ride.arrive_fee else 0),
                            '{0:.2f}'.format(ride.fees if ride.fees else 0),
                            '{0:.2f}'.format(ride.total_cost if ride.total_cost else 0),
                            ride.customer,
                            notes,
                            invoice,
                            ride.cancelled
                            ])

        return response

    else:
        search_form = RideExportForm()

    d = {
        'export_page': True,
        'search_form': search_form
    }

    return render(request, template, d)
