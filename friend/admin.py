from django.contrib import admin

from .models import *


# 好友关系
class FriendAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'state', 'is_block', 'is_abandon', 'update_time']
    search_fields = ('from_user__tel', 'to_user__tel')
    list_filter = ('state', 'is_block', 'is_abandon')


admin.site.register(Friend, FriendAdmin)
