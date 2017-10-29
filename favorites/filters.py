from django_filters.rest_framework import FilterSet
from .models import *


class FavoritesFilter(FilterSet):
    class Meta:
        model = Favorites
        fields = {
            'user': ['exact'],
            'name': ['exact', 'icontains'],
            'category': ['exact'],
            'posts': ['exact'],
            'create_time': ['gte', 'lte'],
            'update_time': ['gte', 'lte'],
        }

