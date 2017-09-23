from datetime import timedelta
from django.utils import timezone

from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated

from common.viewset import ModelViewSet
from common.response import success_response, error_response
from common.constants import FriendState
from user.models import User

from .models import *
from .serializers import *


# 好友关系视图集
class FriendViewSet(ModelViewSet):
    queryset = Friend.objects.all()
    serializer_class = FriendCreateSerializer
    serializer_classes = {
        'create': FriendCreateSerializer,
        'list': FriendCreateSerializer,
        'retrieve': FriendCreateSerializer,
        'update': FriendCreateSerializer,
    }
    permission_classes = (IsAuthenticated,)

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
            friend_from, is_created_from = Friend.objects.get_or_create(from_user=request.user, to_user=to_user)
            if not is_created_from:
                if friend_from.is_block:
                    # 若已拉黑则解除拉黑
                    friend_from.is_block = False
                else:
                    if friend_from.state == FriendState.Accept:
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
        friends = Friend.objects.filter(from_user=request.user, state=FriendState.Accept, is_block=False).all()
        return self.list_queryset(request, friends, *args, **kwargs)

    # 查看待处理的和最近一天添加的好友关系
    # A->我 返回A的集合
    @list_route(methods=['GET'])
    def pending_list(self, request, *args, **kwargs):
        # 设置可查记录的时间段
        start = timezone.now() - timedelta(hours=23, minutes=59, seconds=59)
        friends_new = Friend.objects.filter(to_user=request.user, state=FriendState.Accept, is_block=False,
                                            update_time__gt=start).all()
        friends_pending = Friend.objects.filter(to_user=request.user, state=FriendState.Pending, is_block=False)
        friends = friends_new | friends_pending
        return self.list_queryset(request, friends, *args, **kwargs)

    # 搜索好友
    # Receive ----------------------------------
    # key 关键词
    # 检索作用域有手机号码和姓名
    # @list_route(methods=['POST'])
    # def search(self, request):
    #     key = request.data['key']
    #     queryset = []
    #     for user in User.objects.filter(is_real=True).all():
    #         if key in user.username or key in user.get_full_name():
    #             queryset.append(user)
    #     serializer = UserDetailSerializer(queryset, context={'request': request}, many=True)
    #     return Response(serializer.data)
    #
    # # override PUT /friend/friend_id/
    # # 处理好友请求或者修改备注名
    # # Receive ----------------------------------
    # # remark 备注名
    # # state 对应的处理状态
    # # Return -----------------------------------
    # # 200 修改成功/处理成功
    # # 400-1 数据格式错误 400-2 该好友记录不存在
    # # 400-3 无此权限
    # # 修改备注名称
    # def update(self, request, *args, **kwargs):
    #     try:
    #         friend = Friend.objects.get(pk=kwargs['pk'])
    #         if 'remark' in request.data:
    #             # A->B 只有A有修改备注权限
    #             if request.user == friend.from_user:
    #                 friend.remark = request.data['remark']
    #                 friend.save()
    #                 return Response('修改成功', status=status.HTTP_200_OK)
    #             else:
    #                 return fail_response(3, '无此权限')
    #         elif 'state' in request.data:
    #             state = request.data['state']
    #             # 不处理请求
    #             if state == '0':
    #
    #                 return Response('处理成功', status=status.HTTP_200_OK)
    #             # 接受请求
    #             elif state == '1':
    #                 #  A->B 只有B有接受请求权限
    #                 if request.user == friend.to_user:
    #                     friend.state = state
    #                     friend.save()
    #
    #                     # 反向设置B->A
    #                     try:
    #                         # 再次添加好友
    #                         friend_from = Friend.objects.get(from_user=friend.to_user, to_user=friend.from_user)
    #                         friend_from.state = state
    #                         friend_from.remark = friend.from_user.get_full_name()
    #                         friend_from.save()
    #                     except ObjectDoesNotExist:
    #                         # 第一次添加
    #                         Friend.objects.create(from_user=friend.to_user, to_user=friend.from_user,
    #                                               state=state, remark=friend.from_user.get_full_name())
    #
    #                     # 向用户A推送B通过了他的好友请求
    #                     mipush.push(friend.from_user.id, '请求通过',
    #                                 "用户%s通过了你的好友请求" % (request.user.get_full_name()),
    #                                 {"operation": 'friend_pass'})
    #                     return Response('处理成功', status=status.HTTP_200_OK)
    #                 else:
    #                     return fail_response(3, '无此权限')
    #             # 删除好友
    #             elif state == '2':
    #                 # 关系链两端人物均可删除
    #                 if request.user == friend.from_user or request.user == friend.to_user:
    #                     # friend.state = state
    #                     # friend.save()
    #                     friend.delete()
    #
    #                     # 反向设置B->A
    #                     try:
    #                         friend_from = Friend.objects.get(from_user=friend.to_user, to_user=friend.from_user)
    #                         # friend_from.state = state
    #                         # friend_from.save()
    #                         friend_from.delete()
    #                     except ObjectDoesNotExist:
    #                         pass
    #                     return Response('删除成功', status=status.HTTP_200_OK)
    #                 else:
    #                     return fail_response(3, '无此权限')
    #             else:
    #                 return fail_response(4, '参数错误')
    #         else:
    #             return fail_response(4, '参数错误')
    #     except ObjectDoesNotExist:
    #         return fail_response(2, '该好友记录不存在')
    #     except Exception as e:
    #         return fail_response(1, '%s' % e)
