from common.serializers import *
from common.utils import get_time_filename, validate_image_size, validate_video_size, get_list
from user.serializers import UserListSerializer
from friend.models import Friend
from .models import *


# --------------------------------- 图片 ---------------------------------
# 创建图片
class ImageModifySerializer(ModelSerializer):
    class Meta:
        model = Image
        fields = ('user', 'image')


# 列表图片
class ImageListSerializer(ModelSerializer):
    class Meta:
        model = Image
        fields = ('id', 'image')


# 图片详情
class ImageSerializer(ModelSerializer):
    user = UserListSerializer(read_only=True)

    class Meta:
        model = Image
        fields = ('id', 'user', 'image', 'create_time')


# --------------------------------- 帖子 ---------------------------------
# 创建帖子
class PostModifySerializer(ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(validators=[validate_image_size],
                                     allow_empty_file=False,
                                     use_url=False)
    )

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
                # 判断图片是否属于本帖子、是否有权删除
                image_d_errors = []
                for image_d in Image.objects.filter(id__in=get_list(self.context['request'].data, 'images_delete')):
                    if image_d not in self.instance.images.all():
                        image_d_errors.append('图片(ID:{})不属于本帖子无权删除;'.format(image_d.id))
                    elif image_d.user != self.instance.user:
                        image_d_errors.append('图片(ID:{})无权删除;'.format(image_d.id))
                if len(image_d_errors) != 0:
                    raise ValidationError({'image': image_d_errors})
        return data

    def create(self, validated_data):
        images = validated_data.pop('images')
        post = Post.objects.create(**validated_data)
        if post.category == 1:
            # 多图
            for image in images:
                post.images.add(Image.objects.create(user=post.user, image=image))
        return post

    # images新图片 images_delete待删除图片ID列表
    def update(self, instance, validated_data):
        # 从validated_date移除images为setattr方法做准备
        if 'images' in validated_data:
            images = validated_data.pop('images')
        else:
            images = []

        if instance.category == 1:
            # 更新多图
            for image in images:
                instance.images.add(Image.objects.create(user=instance.user, image=image))
            for image_d in Image.objects.filter(id__in=get_list(self.context['request'].data, 'images_delete'),
                                                user=instance.user):
                instance.images.remove(image_d)

        # 更新实例
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    class Meta:
        model = Post
        fields = ('user', 'status', 'title', 'content', 'category', 'video', 'images', 'place', 'location')
        read_only_fields = ('user',)


# 列表帖子
class PostListSerializer(ModelSerializer):
    user = UserListSerializer(read_only=True)
    images = ImageListSerializer(read_only=True, many=True)

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
                  'location', 'get_likes_count', 'get_comment_count', 'get_status_display', 'get_category_display')


# 帖子详情
class PostSerializer(ModelSerializer):
    user = UserListSerializer(read_only=True)
    images = ImageListSerializer(read_only=True, many=True)
    comments = serializers.SerializerMethodField()

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
                  'location', 'comments', 'get_likes_count', 'get_comment_count', 'get_status_display',
                  'get_category_display')


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
                      Friend.objects.filter(from_user=user, is_block=False).all()]
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


# 创建评论
class CommentListSerializer(ModelSerializer):
    user = UserListSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'user', 'post', 'text', 'parent', 'create_time', 'update_time', 'get_likes_count')


# 创建评论
class CommentSerializer(ModelSerializer):
    user = UserListSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'user', 'post', 'text', 'parent', 'create_time', 'update_time', 'get_likes_count')
