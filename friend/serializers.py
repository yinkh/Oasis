from common.serializers import ModelSerializer

from .models import *


# 好友关系 创建
class FriendCreateSerializer(ModelSerializer):

    class Meta:
        model = Friend
        fields = ('from_user', 'to_user', 'say_hi')
