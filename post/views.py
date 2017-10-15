import logging
from datetime import datetime

from django.db.models import Q
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from rest_framework.decorators import list_route, detail_route
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import UserRateThrottle

from common.permissions import IsPostOwnerOrReadOnly, IsCommentOwnerOrReadOnly
from common.response import success_response, error_response
from common.viewset import ModelViewSet, CreateModelMixin, HumanizationSerializerErrorsMixin, GenericViewSet
from common.exception import VerifyError

from friend.models import Friend

from .models import *
from .serializers import *
from .filters import *

logger = logging.getLogger("info")


# 帖子
class PostViewSet(ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostListSerializer
    serializer_classes = {
        'create': PostModifySerializer,
        'list': PostListSerializer,
        'retrieve': PostSerializer,
        'update': PostModifySerializer,
    }
    permission_classes = (IsAuthenticated,)
    filter_class = PostFilter
    ordering_fields = '__all__'
    search_fields = ('title', 'content', 'user__nickname')

    # 修改、删除需要所有者权限
    def get_permissions(self):
        if self.action in ('update', 'partial_update', 'destroy'):
            self.permission_classes = [IsAuthenticated, IsPostOwnerOrReadOnly, ]
        return super(self.__class__, self).get_permissions()

    # 帖子所有者是自己
    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)

    # 假删除
    def perform_destroy(self, instance):
        instance.is_abandon = True
        instance.save()

    def get_queryset(self):
        # 范围为 公开 好友的故事 我的帖子
        queryset = Post.objects.filter(status=0).all() | self.get_queryset_friend() | \
                   Post.objects.filter(user=self.request.user).all()
        return queryset

    # 好友的故事
    def get_queryset_friend(self):
        my_friends = [friend.to_user for friend in
                      Friend.objects.filter(from_user=self.request.user, is_block=False, is_post_block=False).all()]
        queryset = self.queryset.filter(user__in=my_friends, status=1).all()
        return queryset

    # 我的帖子列表
    def list(self, request, *args, **kwargs):
        queryset = self.queryset.filter(user=request.user)
        return self.list_queryset(request, queryset, *args, **kwargs)

    # 故事列表
    @list_route(methods=['GET'])
    def story_list(self, request, *args, **kwargs):
        return self.list_queryset(request, self.get_queryset_friend(), *args, **kwargs)

    # 帖子列表
    @list_route(methods=['GET'])
    def post_list(self, request, *args, **kwargs):
        queryset = self.queryset.filter(status=0).all()
        return self.list_queryset(request, queryset, *args, **kwargs)

    # 点赞
    @detail_route(methods=['GET'])
    def like(self, request, pk, *args, **kwargs):
        instance = self.get_object()
        instance.likes.add(request.user)
        return success_response('点赞成功')

    # 取消点赞
    @detail_route(methods=['GET'])
    def unlike(self, request, pk, *args, **kwargs):
        # 范围为我点过赞的帖子
        self.queryset = request.user.post_set.all()
        instance = self.get_object()
        instance.likes.remove(request.user)
        return success_response('取消点赞成功')

    # 帖子点赞用户列表(未分页)
    @detail_route(methods=['GET'])
    def likes_list(self, request, pk, *args, **kwargs):
        instance = self.get_object()
        serializer = UserListSerializer(instance.likes, many=True, context=self.get_serializer_context())
        return success_response(serializer.data)


# 评论
class CommentViewSet(ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentListSerializer
    serializer_classes = {
        'create': CommentModifySerializer,
        'list': CommentListSerializer,
        'retrieve': CommentSerializer,
        'update': CommentModifySerializer,
    }
    permission_classes = (IsAuthenticated,)
    page_size = 1
    filter_class = CommentFilter
    ordering_fields = '__all__'
    search_fields = ('text',)

    # 修改、删除需要所有者权限
    def get_permissions(self):
        if self.action in ('update', 'partial_update', 'destroy'):
            self.permission_classes = [IsAuthenticated, IsCommentOwnerOrReadOnly, ]
        return super(self.__class__, self).get_permissions()

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    # 限制评论用户
    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)

    # 禁止修改
    def update(self, request, *args, **kwargs):
        return error_response(1, '禁止修改')

    # 假删除
    def perform_destroy(self, instance):
        # 若删除的为父评论 所有的子评论升级为一级评论
        Comment.objects.filter(parent=instance).update(parent=None)
        instance.is_abandon = True
        instance.save()

    # 点赞
    @detail_route(methods=['GET'])
    def like(self, request, pk, *args, **kwargs):
        instance = self.get_object()
        instance.likes.add(request.user)
        return success_response('点赞成功')

    # 取消点赞
    @detail_route(methods=['GET'])
    def unlike(self, request, pk, *args, **kwargs):
        # 范围为我点过赞的评论
        self.queryset = request.user.comment_set.all()
        instance = self.get_object()
        instance.likes.remove(request.user)
        return success_response('取消点赞成功')

    # 评论点赞用户列表(未分页)
    @detail_route(methods=['GET'])
    def likes_list(self, request, pk, *args, **kwargs):
        instance = self.get_object()
        serializer = UserListSerializer(instance.likes, many=True, context=self.get_serializer_context())
        return success_response(serializer.data)
