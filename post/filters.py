from django_filters.rest_framework import FilterSet
from .models import Post


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
