from django.contrib import admin

from .models import *


# 好友关系
class FriendAdmin(admin.ModelAdmin):
    list_display = ['id', 'from_user', 'to_user', 'state', 'is_block', 'is_abandon', 'agree_time']
    search_fields = ('from_user__tel', 'to_user__tel')
    list_filter = ('state', 'is_block', 'is_abandon')

    def get_queryset(self, request):
        return Friend.all.all()


admin.site.register(Friend, FriendAdmin)
