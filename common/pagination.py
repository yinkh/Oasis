from collections import OrderedDict
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.core.paginator import Paginator, InvalidPage


# 屏蔽UnorderedObjectListWarning
class DjangoPaginator(Paginator):
    def _check_object_list_is_ordered(self):
        """
        Warn if self.object_list is unordered (typically a QuerySet).
        Pagination may yield inconsistent results with an unordered
        """
        pass


# 分页
class Pagination(PageNumberPagination):
    django_paginator_class = DjangoPaginator
    page_number = 1
    page_size_query_param = 'page_size'
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        """
        使用page_size参数限制每页条数
        超出页码范围返回第一页
        最后一页页码用last表示
        """
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = self.django_paginator_class(queryset, page_size)
        self.page_number = request.query_params.get(self.page_query_param, 1)
        if self.page_number in self.last_page_strings:
            self.page_number = paginator.num_pages

        try:
            self.page = paginator.page(self.page_number)
        except InvalidPage:
            # 非法页码返回第一页
            self.page_number = '1'
            self.page = paginator.page(self.page_number)

        if paginator.num_pages > 1 and self.template is not None:
            # The browsable API should display pagination controls.
            self.display_page_controls = True

        self.request = request
        return list(self.page)

    def get_page_size(self, request):
        """
        page_size > 0 使用新page_size
        page_size = 0 时不分页
        page_size < 0 时使用默认page_size
        """
        if self.page_size_query_param:
            page_size = min(int(request.query_params.get(self.page_size_query_param, self.page_size)),
                            self.max_page_size)
            if page_size > 0:
                return page_size
            elif page_size == 0:
                return None
            else:
                pass
        return self.page_size

    def get_paginated_response(self, data):
        """
        count 总条数
        num_pages 总页数
        page_num 页码
        :param data: 
        :return: 
        """
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('page_num', self.page.paginator.num_pages),
            ('page_no', int(self.page_number)),
            ('next', self.get_next_link() if self.get_next_link() else ''),
            ('previous', self.get_previous_link() if self.get_previous_link() else ''),
            ('results', data)
        ]))
