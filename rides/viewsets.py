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

        # DEBUG request
        # import pprint
        # pp = pprint.PrettyPrinter(indent=4)
        # print
        # pp.pprint(dict(request.GET))
        # print

        # ORDERING (1-dimensional)
        dt = request.GET
        order_param = dt.get('columns[{}][data]'.format(int(dt.get('order[0][column]', '0'))))
        order_dir = '-' if dt.get('order[0][dir]', 'asc') == 'desc' else ''
        order = '{}{}'.format(order_dir, order_param)

        print
        print order
        print

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
