from common.serializers import ModelSerializer

from user.serializers import UserListSerializer

from .models import *


# 好友关系 创建
class FriendCreateSerializer(ModelSerializer):
    class Meta:
        model = Friend
        fields = ('from_user', 'to_user', 'say_hi')


class FriendListSerializer(ModelSerializer):
    from_user = UserListSerializer(read_only=True)
    to_user = UserListSerializer(read_only=True)

    class Meta:
        model = Friend
        fields = ('id', 'from_user', 'to_user', 'state', 'remark', 'say_hi', 'agree_time',
                  'create_time', 'update_time', 'get_state_display')


class FriendFromListSerializer(ModelSerializer):
    from_user = UserListSerializer(read_only=True)

    class Meta:
        model = Friend
        fields = ('id', 'from_user', 'to_user', 'state', 'remark', 'say_hi', 'agree_time',
                  'create_time', 'update_time', 'get_state_display')


class FriendToListSerializer(ModelSerializer):
    to_user = UserListSerializer(read_only=True)

    class Meta:
        model = Friend
        fields = ('id', 'from_user', 'to_user', 'state', 'remark', 'say_hi', 'agree_time',
                  'create_time', 'update_time', 'get_state_display')


class FriendToWithPostListSerializer(ModelSerializer):
    to_user = UserListSerializer(read_only=True)

    class Meta:
        model = Friend
        fields = ('id', 'from_user', 'to_user', 'state', 'remark', 'say_hi', 'agree_time', 'is_post_block',
                  'create_time', 'update_time', 'get_state_display')


class FriendModifySerializer(ModelSerializer):

    class Meta:
        model = Friend
        fields = ('id', 'state', 'remark', 'is_block')
