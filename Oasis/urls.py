from django.conf.urls import url, include
from django.contrib import admin

from rest_framework.routers import DefaultRouter

from user.views import UserViewSet

router = DefaultRouter()
# 用户
router.register(r'user', UserViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^admin/', admin.site.urls),
]
