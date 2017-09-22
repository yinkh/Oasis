from django_filters.rest_framework import FilterSet
from .models import User


class UserFilter(FilterSet):
    class Meta:
        model = User
        fields = {
            'username': ['exact', 'icontains'],
            'tel': ['exact', 'icontains'],
            'gender': ['exact'],
            'name': ['exact', 'icontains'],
            'email': ['exact', 'icontains'],
        }
