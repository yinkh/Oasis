from django_filters.rest_framework import FilterSet
from .models import Friend


class FriendFilter(FilterSet):
    class Meta:
        model = Friend
        fields = {
            'from_user': ['exact'],
            'to_user': ['exact'],
            'state': ['exact', 'in'],
            'is_block': ['exact'],
            'remark': ['exact', 'icontains'],
            'say_hi': ['exact', 'icontains'],
            'agree_time': ['gte', 'lte'],
            'create_time': ['gte', 'lte'],
            'update_time': ['gte', 'lte']
        }
