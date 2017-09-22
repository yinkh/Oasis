from django.contrib import admin
from django.contrib.auth.models import Permission, Group

from common.admin import UserAdmin
from .models import *


# 用户
class MyUserAdmin(UserAdmin):
    list_display = ['id', 'username', 'get_full_name', 'tel', 'gender']
    fieldsets = (
        ('登陆信息', {'fields': ('username', 'tel', 'password')}),
        ('用户信息', {'fields': ('name', 'portrait', 'gender', 'birth_day', 'location', 'introduction')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )
    ordering = ('id',)
    search_fields = ('username', 'name', 'tel')


admin.site.register(User, MyUserAdmin)


# 短信验证码
class TelAdmin(admin.ModelAdmin):
    list_display = ['tel', 'code', 'purpose', 'duration', 'send_time']
    search_fields = ('tel',)


admin.site.register(TelVerify, TelAdmin)
