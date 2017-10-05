from django.contrib import admin

from .models import *


# 帖子
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'status', 'is_abandon', 'time']
    search_fields = ('title',)
    list_filter = ('status', 'is_abandon')
    filter_horizontal = ('photos',)

    def get_queryset(self, request):
        return Post.all.all()


# 图片
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'image')
    search_fields = ('image__name',)


admin.site.register(Post, PostAdmin)
admin.site.register(Photo, PhotoAdmin)
