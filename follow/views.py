from django.db.models import Q

from rest_framework.decorators import list_route, detail_route
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated

from common.mixins import ListModelMixin
from common.response import success_response, error_response

from user.models import User
from user.filters import UserFilter
from user.serializers import UserListSerializer

from .models import *


# 关注
class FollowViewSet(ListModelMixin, GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = (IsAuthenticated,)
    filter_class = UserFilter
    ordering_fields = '__all__'
    search_fields = ('username', 'tel', 'nickname')

    # 空列表
    # override /follow/
    def list(self, request, *args, **kwargs):
        return success_response('')

    # 关注某用户
    # url: /follow/[user_id]/follow/
    # Return -----------------------------------
    # 200 关注成功 400-1 数据格式错误 400-2 用户不存在 400-3 不可关注自己
    @detail_route(methods=['GET'])
    def follow(self, request, pk):
        to_user = self.get_object()
        if to_user != request.user:
            Follow.objects.get_or_create(from_user=request.user, to_user=to_user)
            return success_response('关注成功')
        else:
            return error_response(3, '不可关注自己')

    # 取关某用户
    # url: /follow/[user_id]/unfollow/
    # Return -----------------------------------
    # 200 取消关注成功 400-1 数据格式错误 400-2 用户不存在
    @detail_route(methods=['GET'])
    def unfollow(self, request, pk):
        to_user = self.get_object()
        Follow.objects.filter(from_user=request.user, to_user=to_user).update(is_abandon=True)
        return success_response('取消关注成功')

    # 检测关注状态
    # url: /follow/[user_id]/check/
    # Return -----------------------------------
    # 200 True 已关注 False 未关注
    @detail_route(methods=['GET'])
    def check(self, request, pk):
        to_user = self.get_object()
        if Follow.objects.filter(from_user=request.user, to_user=to_user).exists():
            return success_response(True)
        else:
            return success_response(False)

    # 关注列表
    # url: /follow/follow_list/
    # Return -----------------------------------
    # 200 分页后关注的用户列表
    @list_route(methods=['GET'])
    def follow_list(self, request, *args, **kwargs):
        follows = request.user.follow_from_user.all()
        queryset = User.objects.filter(id__in=[follow.to_user.id for follow in follows])
        return self.list_queryset(request, queryset, *args, **kwargs)

    # 粉丝列表
    # url: /follow/fan_list/
    # Return -----------------------------------
    # 200 分页后关注的粉丝列表
    @list_route(methods=['GET'])
    def fan_list(self, request, *args, **kwargs):
        fans = request.user.follow_to_user.all()
        queryset = User.objects.filter(id__in=[fan.from_user.id for fan in fans])
        return self.list_queryset(request, queryset, *args, **kwargs)
