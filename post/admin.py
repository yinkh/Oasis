from django.contrib import admin

from .models import *


# 帖子
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'status', 'category', 'is_abandon', 'time']
    search_fields = ('title',)
    list_filter = ('status', 'category', 'is_abandon')
    filter_horizontal = ('images', 'likes')

    def get_queryset(self, request):
        return Post.all.all()


# 图片
class ImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'image', 'create_time')
    search_fields = ('image__name',)


admin.site.register(Post, PostAdmin)
admin.site.register(Image, ImageAdmin)
