import xadmin

from django.contrib import admin
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static

from rest_framework.routers import DefaultRouter
from rest_framework_jwt.views import refresh_jwt_token, verify_jwt_token

from user.views import UserViewSet, FileViewSet, AgreementViewSet
from friend.views import FriendViewSet
from follow.views import FollowViewSet
from post.views import PostViewSet, CommentViewSet
from favorites.views import FavoritesViewSet

router = DefaultRouter()
# 用户
router.register(r'user', UserViewSet, base_name='user')
# 文件
router.register(r'file', FileViewSet)
# 协议
router.register(r'agreement', AgreementViewSet)
# 好友
router.register(r'friend', FriendViewSet)
# 关注
router.register(r'follow', FollowViewSet, base_name='follow')
# 帖子
router.register(r'post', PostViewSet)
# 评论
router.register(r'comment', CommentViewSet)
# 收藏夹
router.register(r'favorites', FavoritesViewSet)

urlpatterns = [
    url(r'^user/refresh_token/$', refresh_jwt_token),
    url(r'^user/verify_token/$', verify_jwt_token),
    url(r'^', include(router.urls)),
    url(r'^admin/', admin.site.urls),
    url(r'^xadmin/', xadmin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
