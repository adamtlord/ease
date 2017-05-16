from collections import OrderedDict

from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination


def _get_count(queryset):
    """
    Determine an object count, supporting either querysets or regular lists.
    """
    try:
        return queryset.count()
    except (AttributeError, TypeError):
        return len(queryset)


class DataTablesPagination(LimitOffsetPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    limit_query_param = 'length'
    offset_query_param = 'start'
    max_page_size = 1000

    def paginate_queryset(self, queryset, request, view=None):
        self.count = _get_count(queryset)
        self.limit = self.get_limit(request)
        if self.limit is None:
            return None

        self.offset = self.get_offset(request)
        self.request = request
        if self.count > self.limit and self.template is not None:
            self.display_page_controls = True

        if self.count == 0 or self.offset > self.count:
            return []
        return list(queryset[self.offset:self.offset + self.limit])

    def get_paginated_response(self, data):
        return OrderedDict([
            ('recordsFiltered', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('data', data)
        ])
