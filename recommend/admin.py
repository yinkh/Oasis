from django.contrib import admin
from .models import *


# 推荐
class RecommendAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'date', 'is_abandon']
    list_filter = ('is_abandon',)
    filter_horizontal = ('posts',)

    def get_queryset(self, request):
        return Recommend.all.all()


admin.site.register(Recommend, RecommendAdmin)
