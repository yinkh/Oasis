from django.contrib import admin

from .models import *


# 关注
class FollowAdmin(admin.ModelAdmin):
    list_display = ['id', 'from_user', 'to_user', 'is_abandon', 'update_time', 'create_time']
    search_fields = ('from_user__tel', 'to_user__tel')
    list_filter = ('is_abandon',)

    def get_queryset(self, request):
        return Follow.all.all()


admin.site.register(Follow, FollowAdmin)
