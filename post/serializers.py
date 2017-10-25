from django.conf import settings
from common.serializers import *
from common.utils import get_time_filename, validate_image_ext, validate_video_ext, sizeof_fmt, get_list
from user.models import File
from user.serializers import UserListSerializer, FileInlineSerializer
from friend.models import Friend
from .models import *


# --------------------------------- 帖子 ---------------------------------
# 创建帖子
class PostModifySerializer(ModelSerializer):
    def validate_images(self, data):
        if data:
            errors = []
            for image in data:
                image_errors = []
                if not validate_image_ext(image.ext):
                    image_errors.append('文件 {} 不是合法的图片类型'.format(image.filename))
                if image.file.size > settings.MAX_IMAGE_SIZE:
                    image_errors.append('文件 {} 大小超过{}'.format(image.filename,
                                                              sizeof_fmt(settings.MAX_IMAGE_SIZE)))
                request = self.context['request']
                if image.user and hasattr(request, 'user'):
                    if image.user != request.user:
                        image_errors.append('文件 {} 不是本人上传或者公开图片'.format(image.filename))
                if len(image_errors) != 0:
                    errors.append(';'.join(image_errors))

            if len(errors) != 0:
                raise serializers.ValidationError(errors)
        return data

    def validate_video(self, data):
        if data:
            if not validate_video_ext(data.ext):
                raise serializers.ValidationError('文件 {} 不是非法的视频文件'.format(data.filename))
            if data.file.size > settings.MAX_VIDEO_SIZE:
                raise serializers.ValidationError('文件 {} 大小超过{}'.format(data.filename,
                                                                        sizeof_fmt(settings.MAX_VIDEO_SIZE)))
            request = self.context['request']
            if data.user and hasattr(request, 'user'):
                if data.user != request.user:
                    raise serializers.ValidationError('文件 {} 不是本人上传或者公开视频'.format(data.filename))
        return data

    def validate(self, data):
        if self.instance is None:
            category = data['category']
            if category == 0:
                if 'images' in data and len(data['images']) != 0:
                    raise ValidationError({'images': '视频不接收多图'})
                elif 'video' not in data:
                    raise ValidationError({'video': '视频必传'})
            elif category == 1:
                if 'video' in data:
                    raise ValidationError({'video': '多图不接收视频'})
                elif 'images' not in data or len(data['images']) == 0:
                    raise ValidationError({'images': '多图必传'})
        else:
            category = self.instance.category
            if category == 0:
                if 'images' in data and len(data['images']) != 0:
                    raise ValidationError({'images': '视频不接收多图'})
            elif category == 1:
                if 'video' in data:
                    raise ValidationError({'video': '多图不接收视频'})
        return data

    class Meta:
        model = Post
        fields = ('user', 'status', 'title', 'content', 'category', 'video', 'images', 'place', 'longitude', 'latitude')
        read_only_fields = ('user',)


# 列表帖子
class PostListSerializer(ModelSerializer):
    user = UserListSerializer(read_only=True)
    video = FileInlineSerializer(read_only=True)
    images = FileInlineSerializer(read_only=True, many=True)
    is_liked = serializers.SerializerMethodField()

    def get_is_liked(self, instance):
        return True if self.context['request'].user in instance.likes.all() else False

    def to_representation(self, instance):
        """视频只返回video 图片只返回images"""
        data = super(PostListSerializer, self).to_representation(instance)
        if instance.category == 0:
            data.pop('images', None)
        elif instance.category == 1:
            data.pop('video', None)
        return data

    class Meta:
        model = Post
        fields = ('id', 'user', 'status', 'title', 'content', 'category', 'video', 'images', 'time', 'place',
                  'longitude', 'latitude', 'is_liked', 'get_likes_count', 'get_comment_count', 'get_status_display',
                  'get_category_display')


# 列表帖子(带距离)
class PostDistanceListSerializer(ModelSerializer):
    user = UserListSerializer(read_only=True)
    video = FileInlineSerializer(read_only=True)
    images = FileInlineSerializer(read_only=True, many=True)
    is_liked = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()

    def get_is_liked(self, instance):
        return True if self.context['request'].user in instance.likes.all() else False

    def get_distance(self, instance):
        longitude = self.context['longitude']
        latitude = self.context['latitude']
        from .utils import haversine
        return haversine(longitude, latitude, instance.longitude, instance.latitude)

    def to_representation(self, instance):
        """视频只返回video 图片只返回images"""
        data = super(PostDistanceListSerializer, self).to_representation(instance)
        if instance.category == 0:
            data.pop('images', None)
        elif instance.category == 1:
            data.pop('video', None)
        return data

    class Meta:
        model = Post
        fields = ('id', 'user', 'status', 'title', 'content', 'category', 'video', 'images', 'time', 'place',
                  'longitude', 'latitude', 'is_liked', 'get_likes_count', 'get_comment_count', 'get_status_display',
                  'get_category_display', 'distance')


# 帖子详情
class PostSerializer(ModelSerializer):
    user = UserListSerializer(read_only=True)
    video = FileInlineSerializer(read_only=True)
    images = FileInlineSerializer(read_only=True, many=True)
    comments = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    def get_is_liked(self, instance):
        return True if self.context['request'].user in instance.likes.all() else False

    def to_representation(self, instance):
        """视频只返回video 图片只返回images"""
        data = super(PostSerializer, self).to_representation(instance)
        if instance.category == 0:
            data.pop('images', None)
        elif instance.category == 1:
            data.pop('video', None)
        return data

    def get_comments(self, instance):
        return CommentListSerializer(Comment.objects.filter(post=instance)[:10], many=True, context=self.context).data

    class Meta:
        model = Post
        fields = ('id', 'user', 'status', 'title', 'content', 'category', 'video', 'images', 'time', 'place',
                  'longitude', 'latitude', 'comments', 'is_liked', 'get_likes_count', 'get_comment_count',
                  'get_status_display', 'get_category_display')


# 附近帖子
class PostNearBySerializer(ModelSerializer):
    distance = serializers.DecimalField(max_digits=18, decimal_places=14, min_value=0, required=True, label='距离')

    class Meta:
        model = Post
        fields = ('distance', 'longitude', 'latitude')
        extra_kwargs = {'longitude': {'required': True}, 'latitude': {'required': True}}


# --------------------------------- 评论 ---------------------------------
# 创建评论
class CommentModifySerializer(ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(CommentModifySerializer, self).__init__(*args, **kwargs)
        # 限制有权评论的帖子范围
        self.fields['post'].queryset = self.get_post_queryset()

    def get_post_queryset(self):
        # 范围为 公开 好友的故事 我的帖子
        user = self.context['request'].user
        my_friends = [friend.to_user for friend in
                      Friend.objects.filter(from_user=user, is_block=False, is_post_block=False).all()]
        queryset_friend = Post.objects.filter(user__in=my_friends, status=1).all()
        queryset = Post.objects.filter(status=0).all() | queryset_friend | Post.objects.filter(user=user).all()
        return queryset

    def validate(self, data):
        instance = self.Meta.model(**data)
        instance.clean()
        return data

    class Meta:
        model = Comment
        fields = ('post', 'text', 'parent')


# 评论列表
class CommentListSerializer(ModelSerializer):
    user = UserListSerializer(read_only=True)
    is_liked = serializers.SerializerMethodField()

    # 是否已点赞
    def get_is_liked(self, instance):
        return True if self.context['request'].user in instance.likes.all() else False

    class Meta:
        model = Comment
        fields = ('id', 'user', 'post', 'text', 'parent', 'create_time', 'update_time', 'is_liked', 'get_likes_count')


# 评论详情
class CommentSerializer(ModelSerializer):
    user = UserListSerializer(read_only=True)
    is_liked = serializers.SerializerMethodField()

    # 是否已点赞
    def get_is_liked(self, instance):
        return True if self.context['request'].user in instance.likes.all() else False

    class Meta:
        model = Comment
        fields = ('id', 'user', 'post', 'text', 'parent', 'create_time', 'update_time', 'is_liked', 'get_likes_count')
