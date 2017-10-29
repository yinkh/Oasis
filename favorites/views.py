import logging

from django.db.models import Q

from rest_framework.decorators import list_route, detail_route
from rest_framework.permissions import IsAuthenticated

from common.permissions import IsFavoritesOwnerOrReadOnly
from common.response import success_response, error_response
from common.viewset import ModelViewSet

from .models import *
from .serializers import *
from .filters import *

logger = logging.getLogger("info")


# 收藏夹
class FavoritesViewSet(ModelViewSet):
    queryset = Favorites.objects.all()
    serializer_class = FavoritesListSerializer
    serializer_classes = {
        'create': FavoritesModifySerializer,
        'list': FavoritesListSerializer,
        'retrieve': FavoritesSerializer,
        'update': FavoritesModifySerializer,
    }
    permission_classes = (IsAuthenticated, IsFavoritesOwnerOrReadOnly)
    filter_class = FavoritesFilter
    ordering_fields = '__all__'
    search_fields = ('name',)

    def get_queryset(self):
        queryset = self.queryset.all().filter(Q(user=self.request.user) | Q(category=0))
        return queryset

    # 收藏夹所有者是自己
    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)

    # 假删除
    def perform_destroy(self, instance):
        instance.is_abandon = True
        instance.save()

    # 收藏\取消收藏
    @list_route(methods=['POST'])
    def operate(self, request):
        serializer = FavoritesOperateSerializer(data=request.data, context=self.get_serializer_context())
        if serializer.is_valid():
            data = serializer.validated_data
            if data['operate'] == 0:
                data['favorites'].posts.add(data['post'])
                return success_response('收藏成功')
            else:
                # 取消收藏
                data['favorites'].posts.remove(data['post'])
                return success_response('取消收藏成功')
        else:
            return error_response(1, self.humanize_errors(serializer))
