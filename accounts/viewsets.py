from django.db.models import Count, Max, Q

from rest_framework import viewsets
from rest_framework.response import Response
from accounts.models import CustomUser, Customer
from accounts.serializers import UserSerializer, CustomerSerializer
from common.paginators import DataTablesPagination


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    pagination_class = DataTablesPagination
    # filter_backends = (filters.DjangoFilterBackend,)
    # filter_fields = ('active', 'first_name',)
    # filter_class = CustomerFilter

    def base_queryset(self):
        return Customer.objects.all().annotate(ride_count=Count('rides')).annotate(last_ride_at=Max('rides__start_date'))

    def filter_queryset(self, request):
        queryset = self.base_queryset()

        # DEBUG request
        # import pprint
        # pp = pprint.PrettyPrinter(indent=4)
        # print
        # pp.pprint(dict(request.GET))
        # print

        dt = request.GET

        # FILTERING
        active_filter = dt.get('active')
        if active_filter:
            queryset = queryset.filter(user__is_active=active_filter)

        # SEARCHING
        search_value = dt.get('search[value]', None)
        if search_value:
            for term in search_value.split():
                queryset = queryset.filter(
                    Q(first_name__icontains=term) |
                    Q(last_name__icontains=term) |
                    Q(home_phone__icontains=term) |
                    Q(mobile_phone__icontains=term) |
                    Q(notes__icontains=term)
                )

        # ORDERING (1-dimensional)
        if dt.get('columns[0][data]'):
            order_param = dt.get('columns[{}][data]'.format(int(dt.get('order[0][column]', '0'))), 0)
            if order_param == 'last_ride':
                # not a real field, it's an annotation only guaranteed to be on this queryset
                order_param = 'last_ride_at'
            order_dir = '-' if dt.get('order[0][dir]', 'asc') == 'desc' else ''
            order = '{}{}'.format(order_dir, order_param)

            queryset = queryset.order_by(order)

        return queryset

    def list(self, request):
        queryset = self.filter_queryset(request)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = CustomerSerializer(page, many=True, context={'request': request})
            response = self.get_paginated_response(serializer.data)
            response['draw'] = int(request.GET.get('draw', 1))
            response['recordsTotal'] = len(self.base_queryset())
            return Response(response)

        serializer = CustomerSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
