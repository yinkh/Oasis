from rest_framework import permissions


class IsSelf(permissions.BasePermission):
    """
    检测当前操作的用户是否是自己
    """

    def has_object_permission(self, request, view, obj):
        return obj == request.user


class IsPostOwnerOrReadOnly(permissions.BasePermission):
    """
    检测当前操作的用户是否是帖子所有者
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsCommentOwnerOrReadOnly(permissions.BasePermission):
    """
    检测当前操作的用户是否是评论所有者
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsFileOwnerOrReadOnly(permissions.BasePermission):
    """
    检测当前操作的用户是否是文件所有者
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
