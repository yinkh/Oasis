from django.conf.urls import url, include
from django.contrib import admin

from rest_framework.routers import DefaultRouter
from rest_framework_jwt.views import refresh_jwt_token, verify_jwt_token

from user.views import UserViewSet, AgreementViewSet

router = DefaultRouter()
# 用户
router.register(r'user', UserViewSet)
# 协议
router.register(r'agreement', AgreementViewSet)

urlpatterns = [
    url(r'^user/refresh_token/$', refresh_jwt_token),
    url(r'^user/verify_token/$', verify_jwt_token),
    url(r'^', include(router.urls)),
    url(r'^admin/', admin.site.urls),
]
