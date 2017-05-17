from django.db.models import Q

from rest_framework import viewsets
from rest_framework.response import Response

from common.paginators import DataTablesPagination
from rides.models import Ride, Destination
from rides.serializers import RideSerializer, DestinationSerializer


class RideViewSet(viewsets.ModelViewSet):
    queryset = Ride.objects.all()
    serializer_class = RideSerializer
    pagination_class = DataTablesPagination

    def base_queryset(self):
        return Ride.objects.all()

    def filter_queryset(self, request):
        queryset = self.base_queryset()

        dt = request.GET

        # FILTERING
        invoiced_filter = dt.get('invoiced')
        if invoiced_filter:
            queryset = queryset.filter(invoiced=invoiced_filter)

        # SEARCHING
        search_value = dt.get('search[value]', None)
        if search_value:
            for term in search_value.split():
                queryset = queryset.filter(
                    Q(customer__first_name__icontains=term) |
                    Q(customer__last_name__icontains=term) |
                    Q(start__name__icontains=term) |
                    Q(start__street1__icontains=term) |
                    Q(start__street2__icontains=term) |
                    Q(start__city__icontains=term) |
                    Q(destination__name__icontains=term) |
                    Q(destination__street1__icontains=term) |
                    Q(destination__street2__icontains=term) |
                    Q(destination__city__icontains=term)
                )

        # ORDERING (1-dimensional)
        if dt.get('columns[0][data]'):
            order_param = dt.get('columns[{}][data]'.format(int(dt.get('order[0][column]', '0'))))
            order_dir = '-' if dt.get('order[0][dir]', 'asc') == 'desc' else ''
            order = '{}{}'.format(order_dir, order_param)

            queryset = queryset.order_by(order)

        return queryset

    def list(self, request):
        queryset = self.filter_queryset(request)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = RideSerializer(page, many=True, context={'request': request})
            response = self.get_paginated_response(serializer.data)
            response['draw'] = int(request.GET.get('draw', 1))
            response['recordsTotal'] = len(self.base_queryset())
            return Response(response)

        serializer = RideSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class DestinationViewSet(viewsets.ModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer
