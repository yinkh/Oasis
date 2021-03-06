import logging
from datetime import datetime, timedelta

from rest_framework.decorators import list_route, detail_route
from rest_framework.permissions import IsAuthenticated

from common.permissions import IsPostOwnerOrReadOnly, IsCommentOwnerOrReadOnly
from common.response import success_response, error_response
from common.viewset import ModelViewSet
from common.exception import PushError
from common import jpush

from recommend.models import Recommend

from .models import *
from .serializers import *
from .filters import *
from .utils import bounding_box, haversine, get_post_queryset

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
        queryset = Post.objects.filter(status=0) | self.get_queryset_friend() | Post.objects.filter(
            user=self.request.user)
        return queryset

    # 好友的故事
    def get_queryset_friend(self):
        my_friends = [friend.to_user for friend in
                      Friend.objects.filter(from_user=self.request.user, is_block=False, is_post_block=False).all()]
        queryset = self.queryset.filter(user__in=my_friends, status=1)
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
        queryset = self.queryset.filter(status=0)
        return self.list_queryset(request, queryset, *args, **kwargs)

    # 点赞
    @detail_route(methods=['GET'])
    def like(self, request, pk, *args, **kwargs):
        instance = self.get_object()
        instance.likes.add(request.user)
        # TODO 向贴主推送点赞
        try:
            jpush.audience(instance.user.id, '帖子点赞',
                           "用户{}赞了您的帖子".format(request.user.get_full_name(user=instance.user)),
                           {'operation': 'post_like', 'post': instance.id})
        except PushError as e:
            logging.error('{} {}'.format(e.code, e.message))
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

    # 附近帖子
    @list_route(methods=['POST'])
    def nearby_posts(self, request, *args, **kwargs):
        serializer = PostNearBySerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            longitude = float(data['longitude'])
            latitude = float(data['latitude'])
            distance = float(data['distance'])
            lon_min, lon_max, lat_min, lat_max = bounding_box(longitude, latitude, distance)
            # 正方形内帖子
            box_queryset = self.get_queryset().filter(longitude__gte=lon_min, longitude__lte=lon_max,
                                                      latitude__gte=lat_min, latitude__lte=lat_max)
            # 正方形内筛选圆形区域
            ids = []
            for x in box_queryset:
                if haversine(longitude, latitude, x.longitude, x.latitude) <= distance:
                    ids.append(x.id)
            queryset = box_queryset.filter(id__in=ids)
            # list部分
            queryset = self.filter_queryset(queryset)
            context = self.get_serializer_context()
            context.update({'longitude': longitude, 'latitude': latitude})

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = PostDistanceListSerializer(page, context=context, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, context=context, many=True)
            return success_response(serializer.data)
        else:
            return error_response(1, self.humanize_errors(serializer))

    # 推荐帖子
    @list_route(methods=['GET'])
    def recommend_posts(self, request, *args, **kwargs):
        recommend = Recommend.objects.filter(date__gte=datetime.now().date() - timedelta(days=10),
                                             date__lte=datetime.now().date()).order_by('-date').first()
        queryset = recommend.posts.all() if recommend else Post.objects.none()
        return self.list_queryset(request, queryset, *args, **kwargs)


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
        return self.queryset.filter(post__in=get_post_queryset(self.request.user))

    # 限制评论用户
    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        # TODO 向贴主推送评论
        try:
            jpush.audience(instance.post.user.id, '帖子评论',
                           "用户{}评论了您的帖子".format(instance.user.get_full_name(user=instance.post.user)),
                           {'operation': 'post_comment', 'post': instance.post.id})
        except PushError as e:
            logging.error('{} {}'.format(e.code, e.message))

        # TODO 回帖向回帖人推送回复
        if instance.parent:
            try:
                jpush.audience(instance.parent.post.user.id, '帖子评论回复',
                               "用户{}回复了您的评论".format(instance.user.get_full_name(user=instance.parent.post.user)),
                               {'operation': 'post_comment', 'post': instance.post.id})
            except PushError as e:
                logging.error('{} {}'.format(e.code, e.message))
        return instance

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
        # TODO 向评论人推送点赞
        try:
            jpush.audience(instance.user.id, '评论点赞',
                           "用户{}赞了您的评论".format(request.user.get_full_name(instance.user)),
                           {'operation': 'comment_like', 'post': instance.post.id})
        except PushError as e:
            logging.error('{} {}'.format(e.code, e.message))
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
