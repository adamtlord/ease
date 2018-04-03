import re
import operator
from functools import reduce
from django.db.models import Q

from rest_framework import viewsets
from rest_framework.response import Response

from common.paginators import DataTablesPagination
from rides.models import Ride, Destination
from rides.serializers import RideSerializer, DestinationSerializer

def assemble_dt_dict(request_dict):
    """
    DataTables sends lots and lots of GET params to give the backend instructions
    for ordering, filtering, and paginating. We need to translate all those strings
    into Python dict so we know what we're supposed to do.
    """

    # This may be helpful for understanding the request dict:
    # import pprint
    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(request_dict)

    # 'columns' will be used for filtering, 'order' for sorting (ordering by column values)
    columns_dict = {
        'columns': {},
        'order': {}
    }

    for key in request_dict:
        if 'columns' in key:
            # Typical params follow this pattern. Translate this to Python:
            # 'columns[0][data]': 'id',
            # 'columns[0][name]': '',
            # 'columns[0][orderable]': 'true',
            # 'columns[0][search][regex]': 'false',
            # 'columns[0][search][value]': '',
            # 'columns[0][searchable]': 'true',
            try:
                col_idx = re.match('columns\[(\d+)\]', key).group(1)
                if col_idx in columns_dict['columns']:
                    continue
                else:
                    col_prefix = 'columns[{}]'.format(col_idx)
                    data = request_dict[col_prefix + '[data]']
                    columns_dict['columns'][col_idx] = {
                        'data': data,
                        'name': request_dict[col_prefix + '[name]'],
                        'orderable': request_dict[col_prefix + '[orderable]'] == 'true',
                        'search_regex': request_dict[col_prefix + '[search][regex]'] == 'true',
                        'search_value': request_dict[col_prefix + '[search][value]'],
                        'searchable': request_dict[col_prefix + '[searchable]'] == 'true',
                    }
            except AttributeError:
                continue
        if 'order' in key:
            # Typical ordering params are a 2-d array of column index and direction
            # 'order[0][column]': '4',
            # 'order[0][dir]': 'desc',
            # 'order[2][column]': '2',
            # 'order[2][dir]': 'asc',
            # The above would translate as "first order by column 4 descending, then order by column 2 ascending"
            try:
                order_idx = re.match('order\[(\d+)\]', key).group(1)
                if order_idx in columns_dict['order']:
                    continue
                else:
                    columns_dict['order'][order_idx] = {
                        'column': request_dict['order[' + order_idx + '][column]'],
                        'dir': request_dict['order[' + order_idx + '][dir]']
                    }
            except AttributeError:
                continue
        else:
            continue

    return columns_dict


def get_ride_ordering(queryset, dt_dict):

    # Not all fields map directly to a Document attribute. For related objects,
    # we need to translate these fields from the serializer back to their ORM relationships
    field_order_map = {
        'id': 'id',
        'start_date': 'start_date',
        'customer.last_name': 'customer__last_name',
        'start': 'start__name',
        'destination': 'destination__name',
        'included_in_plan': 'included_in_plan',
        'distance': 'distance',
        'company': 'company'
    }

    # We use the col_dict to get the 'data' param that corresponds to the given
    # column index
    order_dict = dt_dict['order']
    col_dict = dt_dict['columns']
    ordering = []

    for key in order_dict:
        col_idx = order_dict[key]['column']
        field_name = field_order_map[col_dict[col_idx]['data']]
        direction = '-' if order_dict[key]['dir'] == 'desc' else ''
        ordering.append(direction + field_name)
    return ordering


def filter_ride_table(request_dict, queryset):
    # First translate DataTables' GET params to something we can read
    dt_dict = assemble_dt_dict(request_dict)
    filters = []

    global_filters = []
    global_search = request_dict['search[value]']

    columns_dict = dt_dict['columns']
    # iterate over the table's columns
    for col in list(columns_dict.values()):
        # if the column is searchable and it is being searched against,
        # we need to create a filter for it. However, because each field in the
        # serialized object does not necessarily correspond to a simple Document attribute,
        # we need to construct the filters individually
        if col['searchable']:
            field = col['data']
            query = col['search_value']
            if field == 'id':
                if global_search.isdigit():
                    global_filters.append(Q(id=global_search))
                if query.isdigit():
                    filters.append(Q(id=query))
            if field == 'customer.last_name':
                if global_search:
                    global_q = global_search.split(' ')
                    for q in global_q:
                        global_filters.append(Q(Q(customer__first_name__icontains=q) | Q(customer__last_name__icontains=q)))
                q_list = query.split(' ')
                for q in q_list:
                    filters.append(Q(Q(customer__first_name__icontains=q) | Q(customer__last_name__icontains=q)))
            if field == 'start':
                if global_search:
                    global_q = global_search.split(' ')
                    for q in global_q:
                        global_filters.append(Q(Q(start__name__icontains=q) | Q(start__street1__icontains=q)))
                q_list = query.split(' ')
                for q in q_list:
                    filters.append(Q(Q(start__name__icontains=q) | Q(start__street1__icontains=q)))
            if field == 'destination':
                if global_search:
                    global_q = global_search.split(' ')
                    for q in global_q:
                        global_filters.append(Q(Q(destination__name__icontains=q) | Q(destination__street1__icontains=q)))
                q_list = query.split(' ')
                for q in q_list:
                    filters.append(Q(Q(destination__name__icontains=q) | Q(destination__street1__icontains=q)))

    if global_filters:
        # Join all of the global Q objects with OR so it searches all the fields we want it to
        global_query = reduce(operator.or_, global_filters)
    else:
        global_query = Q()

    if filters:
        # Join all of the Q objects with AND so all the filters work toegether
        filter_query = reduce(operator.and_, filters)
    else:
        filter_query = Q()

    combined_query = Q(global_query & filter_query)

    queryset = queryset.filter(combined_query)

    # We have our queryset, now order it based on which column(s) and direction is selected
    ordering = get_ride_ordering(queryset, dt_dict)

    if ordering:
        # the * operator translates our list of order_by statements into args
        return queryset.order_by(*ordering)

    return queryset


class RideViewSet(viewsets.ModelViewSet):
    queryset = Ride.objects.all()
    serializer_class = RideSerializer
    pagination_class = DataTablesPagination

    def base_queryset(self):
        return Ride.objects.all() \
            .select_related('customer') \
            .select_related('start') \
            .select_related('destination')

    def filter_queryset(self, request):
        queryset = self.base_queryset()

        dt = request.GET

        # FILTERING
        invoiced_filter = dt.get('invoiced')
        if invoiced_filter:
            queryset = queryset.filter(invoiced=invoiced_filter)

        filtered_queryset = filter_ride_table(dt, queryset)

        return filtered_queryset

    def list(self, request):
        queryset = self.filter_queryset(request)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = RideSerializer(page, many=True, context={'request': request})
            response = self.get_paginated_response(serializer.data)
            response['draw'] = int(request.GET.get('draw', 1))
            response['recordsTotal'] = len(self.base_queryset())
            response['draw'] = int(request.GET.get('draw', 1))
            return Response(response)

        serializer = RideSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class DestinationViewSet(viewsets.ModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer
