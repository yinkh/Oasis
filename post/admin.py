from django.contrib import admin

from .models import *


# 图片
class ImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'image', 'create_time')
    search_fields = ('image__name',)


# 帖子
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'status', 'category', 'is_abandon', 'time']
    search_fields = ('title',)
    list_filter = ('status', 'category', 'is_abandon')
    filter_horizontal = ('images', 'likes')

    def get_queryset(self, request):
        return Post.all.all()


# 评论
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post', 'parent', 'create_time', 'is_abandon')
    search_fields = ('text',)
    list_filter = ('is_abandon',)
    filter_horizontal = ('likes',)

    def get_queryset(self, request):
        return Comment.all.all()


admin.site.register(Image, ImageAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
