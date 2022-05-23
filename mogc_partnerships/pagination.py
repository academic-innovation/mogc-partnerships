from edx_rest_framework_extensions.paginators import DefaultPagination


class LargeResultsSetPagination(DefaultPagination):
    page_size = 1000
    max_page_size = 10000
