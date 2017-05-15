from rest_framework.pagination import LimitOffsetPagination


class DataTablesPagination(LimitOffsetPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    limit_query_param = 'length'
    offset_query_param = 'start'
    max_page_size = 1000
