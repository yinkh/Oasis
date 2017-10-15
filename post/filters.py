from django_filters.rest_framework import FilterSet
from .models import *


class PostFilter(FilterSet):
    class Meta:
        model = Post
        fields = {
            'user': ['exact'],
            'status': ['exact'],
            'title': ['exact', 'icontains'],
            'content': ['exact', 'icontains'],
            'category': ['exact'],
            'time': ['gte', 'lte'],
            'likes': ['exact'],
        }


class CommentFilter(FilterSet):
    class Meta:
        model = Comment
        fields = {
            'user': ['exact'],
            'post': ['exact'],
            'text': ['exact', 'icontains'],
            'create_time': ['gte', 'lte'],
            'update_time': ['gte', 'lte'],
            'likes': ['exact'],
        }

