from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated

from common.viewset import ModelViewSet
from common.response import success_response, error_response
from common.constants import FriendState
from common.utils import isdigit, str2bool
from user.models import User

from .models import *
from .serializers import *
from .filters import *


# 好友关系视图集
class FriendViewSet(ModelViewSet):
    queryset = Friend.objects.none()
    serializer_class = FriendCreateSerializer
    serializer_classes = {
        'create': FriendCreateSerializer,
        'list': FriendListSerializer,
        'list_from': FriendFromListSerializer,
        'list_to': FriendToListSerializer,
        'retrieve': FriendListSerializer,
        'update': FriendModifySerializer,
    }
    permission_classes = (IsAuthenticated,)
    filter_class = FriendFilter
    ordering_fields = '__all__'
    search_fields = ('to_user__username', 'to_user__nickname', 'to_user__tel', 'remark')

    def get_queryset(self):
        user = self.request.user
        return Friend.objects.filter(Q(from_user=user) | Q(to_user=user))

    def get_serializer_class(self):
        try:
            return self.serializer_classes[self.action]
        except (KeyError, AttributeError):
            if self.action == 'partial_update':
                return self.serializer_classes['update']
            elif self.action == 'bulk_update':
                return self.serializer_classes['update']
            elif self.action == 'list_from':
                return self.serializer_classes['list_from']
            elif self.action == 'list_to':
                return self.serializer_classes['list_to']
            return self.serializer_class

    # override POST /friend/
    # 请求添加好友
    # Receive ----------------------------------
    # to_user 请求添加用户ID
    # say_hi 验证消息
    # remark 备注
    # Return -----------------------------------
    # 200 请求已发送 400-1 数据格式错误 400-2 该用户不存在 400-3 不可重复添加好友
    # 新建 我->to_user
    def create(self, request, *args, **kwargs):
        try:
            to_user = User.objects.get(id=request.data['to_user'])
            # 我->他人 关系处理
            friend_from, is_created_from = self.get_queryset().get_or_create(from_user=request.user, to_user=to_user)
            if not is_created_from:
                if friend_from.is_block:
                    # 若已拉黑则解除拉黑
                    friend_from.is_block = False
                else:
                    if friend_from.state == FriendState.Agree:
                        return error_response(3, '不可重复添加好友')
            friend_from.state = 1
            friend_from.say_hi = request.data['say_hi']
            if 'remark' in request.data:
                friend_from.remark = request.data['remark']
            else:
                friend_from.remark = to_user.get_full_name()
            friend_from.save()
            # TODO 向他人推送我请求加他为好友
            return success_response('请求已发送')
        except User.DoesNotExist:
            return error_response(2, '该用户不存在')
        except Exception as e:
            return error_response(1, str(e))

    # override GET /friend/
    # 我->B 返回B的集合
    # 查看我的好友列表
    def list(self, request, *args, **kwargs):
        self.action = 'list_to'
        friends = self.get_queryset().filter(from_user=request.user, state=FriendState.Agree, is_block=False).all()
        return self.list_queryset(request, friends, *args, **kwargs)

    # 查看待处理的和最近一天添加的好友关系
    # A->我 已同意 返回一天内A的集合 添加我的新朋友
    # A->我 待处理 返回A的集合 我的待处理
    # 我->B 待处理 返回B的集合 我的待被处理的添加请求
    @list_route(methods=['GET'])
    def pending_list(self, request, *args, **kwargs):
        self.action = 'list'
        queryset = self.get_queryset()
        # 设置可查记录的时间段
        start = timezone.now() - timedelta(hours=23, minutes=59, seconds=59)
        # 添加我的新朋友
        friends_new = queryset.filter(to_user=request.user, state=FriendState.Agree, is_block=False,
                                      agree_time__gt=start).all()
        # 我的待处理
        friends_pending = queryset.filter(to_user=request.user, state=FriendState.Pending, is_block=False)
        # 我拉黑的用户
        friends_block = queryset.filter(from_user=request.user, is_block=True)
        # 不处理已拉黑用户的请求
        friends_pending = friends_pending.exclude(from_user__in=[friend.to_user for friend in friends_block]).all()
        # 我的待被处理的添加请求
        friends_send = queryset.filter(from_user=request.user, state=FriendState.Pending, is_block=False)
        friends = friends_new | friends_pending | friends_send
        return self.list_queryset(request, friends, *args, **kwargs)

    # 查看黑名单
    # 我->B 返回拉黑B的集合
    @list_route(methods=['GET'])
    def black_list(self, request, *args, **kwargs):
        self.action = 'list_to'
        friends_block = self.get_queryset().filter(from_user=request.user, is_block=True)
        return self.list_queryset(request, friends_block, *args, **kwargs)

    # override PATCH /friend/friend_id/
    # 处理好友请求 / 修改备注名 / 拉黑、取消拉黑用户
    # Receive ----------------------------------
    # remark 备注名
    # state 对应的处理状态
    # is_block 是否拉黑 true/false yes/no
    # Return -----------------------------------
    # 200 修改成功/处理成功
    # 400-1 数据格式错误 400-2 该好友记录不存在
    # 400-3 无此权限 400-4 参数错误
    def update(self, request, *args, **kwargs):
        friend = self.get_object()
        try:
            if 'remark' in request.data:
                # A->B 只有A有修改备注权限
                if request.user == friend.from_user:
                    friend.remark = request.data['remark']
                    friend.save()
                    return success_response('设置备注成功')
                else:
                    return error_response(3, '无此权限')
            elif 'is_block' in request.data:
                # A->B 只有A有拉黑权限
                if request.user == friend.from_user:
                    is_block = str2bool(request.data['is_block'])
                    if is_block is not None:
                        friend.is_block = is_block
                        friend.save()
                        if is_block:
                            return success_response('拉黑用户成功')
                        else:
                            return success_response('取消拉黑成功')
                    else:
                        return error_response(4, '参数错误(请输入合法布尔值)')
                else:
                    return error_response(3, '无此权限')
            elif 'state' in request.data:
                # A->B 只有B有接受/拒绝请求权限
                if request.user == friend.to_user:
                    if friend.state == FriendState.Pending:
                        if isdigit(request.data['state']):
                            state = int(request.data['state'])
                            # 接受请求
                            if state == FriendState.Agree:
                                friend.state = state
                                friend.agree_time = timezone.now()
                                friend.save()
                                # 反向设置B->A
                                friend_from, is_created = self.get_queryset().get_or_create(from_user=friend.to_user,
                                                                                            to_user=friend.from_user)
                                friend_from.state = state
                                friend_from.agree_time = timezone.now()
                                friend_from.remark = friend.from_user.get_full_name()
                                friend_from.save()
                                # TODO 向用户A推送B通过了他的好友请求
                                return success_response('添加好友成功')
                            # 拒绝请求
                            elif state == FriendState.Reject:
                                friend.state = state
                                friend.save()
                                return success_response('拒绝请求成功')
                            else:
                                return error_response(4, '参数错误')
                        else:
                            return error_response(4, '参数错误(state为数字)')
                    else:
                        return error_response(5, '不可再次处理该请求')
                else:
                    return error_response(3, '无此权限')
            else:
                return error_response(4, '参数错误')
        except Exception as e:
            import traceback
            traceback.print_exc()
            return error_response(1, str(e))

    # override DELETE /friend/friend_id/
    # 删除我的好友
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user == instance.from_user:
            self.perform_destroy(instance)
            return success_response('删除成功')
        else:
            return error_response(1, '无此权限')

    def perform_destroy(self, instance):
        instance.is_abandon = True
        instance.save()
