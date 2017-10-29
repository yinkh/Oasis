from common.serializers import *
from friend.models import Friend
from post.models import Post
from post.utils import get_post_queryset
from user.serializers import UserListSerializer, FileInlineSerializer
from post.serializers import PostListSerializer
from .models import *


# --------------------------------- 收藏夹 ---------------------------------
# 创建收藏夹
class FavoritesModifySerializer(ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(FavoritesModifySerializer, self).__init__(*args, **kwargs)
        # 限制有权收藏的帖子范围
        self.fields['posts'].queryset = get_post_queryset(self.context['request'].user)

    def validate_cover(self, data):
        if data:
            request = self.context['request']
            if data.user and hasattr(request, 'user'):
                if data.user != request.user:
                    raise serializers.ValidationError('文件 {} 不是本人上传或者公开文件'.format(data.filename))
        return data

    def validate_posts(self, data):
        if data:
            for post in data:
                if post not in self.fields['posts'].queryset:
                    raise serializers.ValidationError('无权收藏帖子 {}'.format(post.title))
        return data

    class Meta:
        model = Favorites
        fields = ('user', 'name', 'cover', 'category', 'posts')
        read_only_fields = ('user',)


# 列表收藏夹
class FavoritesListSerializer(ModelSerializer):
    user = UserListSerializer(read_only=True)
    cover = FileInlineSerializer(read_only=True)

    class Meta:
        model = Favorites
        fields = ('id', 'user', 'name', 'cover', 'category', 'posts', 'get_category_display')


# 收藏夹详情
class FavoritesSerializer(ModelSerializer):
    user = UserListSerializer(read_only=True)
    cover = FileInlineSerializer(read_only=True)
    posts = PostListSerializer(read_only=True, many=True)

    class Meta:
        model = Favorites
        fields = ('id', 'user', 'name', 'cover', 'category', 'posts', 'get_category_display')


# 收藏夹 收藏、取消收藏
class FavoritesOperateSerializer(serializers.Serializer):
    favorites = serializers.PrimaryKeyRelatedField(queryset=Favorites.objects.none(), label='收藏夹')
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.none(), label='帖子')
    operate = serializers.ChoiceField(choices=[0, 1], allow_blank=False, label='操作')

    def __init__(self, *args, **kwargs):
        super(FavoritesOperateSerializer, self).__init__(*args, **kwargs)
        # 限制可操作收藏夹范围
        self.fields['favorites'].queryset = Favorites.objects.filter(user=self.context['request'].user)
        # 限制有权收藏的帖子范围
        self.fields['post'].queryset = get_post_queryset(self.context['request'].user)
