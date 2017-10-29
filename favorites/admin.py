from django.contrib import admin
from .models import *


# 评论
class FavoritesAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'category', 'cover', 'create_time', 'is_abandon')
    search_fields = ('name',)
    list_filter = ('category', 'is_abandon',)
    filter_horizontal = ('posts',)

    def get_queryset(self, request):
        return Favorites.all.all()


admin.site.register(Favorites, FavoritesAdmin)
