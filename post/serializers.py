from common.serializers import *
from user.serializers import UserListSerializer
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
        fields = ('user', 'image', 'create_time')


# 图片详情
class ImageSerializer(ModelSerializer):
    user = UserListSerializer(read_only=True)

    class Meta:
        model = Image
        fields = ('user', 'image', 'create_time')


# --------------------------------- 帖子 ---------------------------------
# 创建帖子
class PostModifySerializer(ModelSerializer):

    class Meta:
        model = Post
        fields = ('user', 'status', 'title', 'content', 'category', 'video', 'images', 'place', 'location')
        extra_kwargs = {'user': {'required': False}}


# 列表帖子
class PostListSerializer(DynamicFieldsModelSerializer):
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
                  'location')


# 帖子详情
class PostSerializer(DynamicFieldsModelSerializer):
    user = UserListSerializer(read_only=True)
    images = ImageListSerializer(read_only=True, many=True)

    class Meta:
        model = Post
        fields = ('id', 'user', 'status', 'title', 'content', 'category', 'video', 'images', 'time', 'place',
                  'location', 'get_status_display', 'get_category_display')
