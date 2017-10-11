import logging

from datetime import datetime
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from django.db.models import Q
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import UserRateThrottle

from common.permissions import IsSelf
from common.response import success_response, error_response
from common.viewset import ModelViewSet, CreateModelMixin, HumanizationSerializerErrorsMixin, GenericViewSet
from common.exception import VerifyError

from friend.models import Friend

from .models import *
from .serializers import *

logger = logging.getLogger("info")


# 帖子
class PostViewSet(ModelViewSet):
    queryset = Post.objects.none()
    serializer_class = UserCreateSerializer
    serializer_classes = {
        'create': UserCreateSerializer,
        'list': UserListSerializer,
        'retrieve': UserSerializer,
        'update': UserModifySerializer,
    }
    # 403 错误均为未登录
    permission_classes = (IsAuthenticated,)
    filter_class = UserFilter
    ordering_fields = '__all__'
    search_fields = ('username', 'tel', 'nickname')
