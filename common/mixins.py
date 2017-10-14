"""
Basic building blocks for generic class based views.

We don't bind behaviour to http method handlers yet,
which allows mixin classes to be composed in interesting ways.
"""
from __future__ import unicode_literals
import ast
from django.core.exceptions import FieldDoesNotExist
from common.response import success_response, error_response


class CreateModelMixin(object):
    """
    Create a model instance.
    """

    def create(self, request, *args, **kwargs):
        self.before_create()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            instance = self.perform_create(serializer)
            return success_response(self.serializer_classes['retrieve'](instance,
                                                                        context=self.get_serializer_context()
                                                                        ).data)
        else:
            return error_response(1, self.humanize_errors(serializer))

    # 新增之前
    def before_create(self):
        pass

    # 执行新增
    def perform_create(self, serializer):
        return serializer.save()


class ListModelMixin(object):
    """
    List a queryset.
    """

    def list(self, request, *args, **kwargs):
        self.before_list()
        queryset = self.get_queryset()
        return self.list_queryset(request, queryset, *args, **kwargs)

    def list_queryset(self, request, queryset, *args, **kwargs):
        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

    def before_list(self):
        pass


class RetrieveModelMixin(object):
    """
    Retrieve a model instance.
    """

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        self.before_retrieve(instance)
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def before_retrieve(self, instance):
        pass


class UpdateModelMixin(object):
    """
    Update a model instance.
    """

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        self.before_update(instance)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}

            return success_response(self.serializer_classes['retrieve'](instance,
                                                                        context=self.get_serializer_context()
                                                                        ).data)
        else:
            return error_response(1, self.humanize_errors(serializer))

    def before_update(self, instance):
        pass

    def perform_update(self, serializer):
        return serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class DestroyModelMixin(object):
    """
    Destroy a model instance.
    """

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.before_destroy(instance)
        self.perform_destroy(instance)
        return success_response('删除成功')

    def before_destroy(self, instance):
        pass

    def perform_destroy(self, instance):
        instance.delete()


class MultiSerializerMixin(object):
    """
    serializer_classes = {
        'create': GroupModifySerializer,
        'list': GroupListSerializer,
        'retrieve': GroupSerializer,
        'update': GroupModifySerializer,
    }
    """

    def get_serializer_class(self):
        try:
            return self.serializer_classes[self.action]
        except (KeyError, AttributeError):
            if self.action == 'partial_update':
                return self.serializer_classes['update']
            elif self.action == 'bulk_update':
                return self.serializer_classes['update']
            return self.serializer_class


# 将serializer中的错误解析为交互更友好的形式
class HumanizationSerializerErrorsMixin(object):
    # humanization_serializer_errors
    def humanize_errors(self, serializer):
        """
        :param serializer: 序列化类
        :return: 交互友好的错误提示
        """
        humanization_errors = []
        try:
            model = serializer.Meta.model
        except AttributeError:
            # 参数错误 最可能原因 该serializer不是ModelSerializer没有Meta属性
            model = self.get_queryset().model
        for key, values in serializer.errors.items():
            try:
                # 字段对应的verbose_name
                verbose_name = model._meta.get_field(key).verbose_name
            except FieldDoesNotExist:
                # 模型对应的verbose_name
                verbose_name = model._meta.verbose_name
            humanization_errors.append('{}:{}'.format(verbose_name, ' '.join(values)))
        return '; '.join(humanization_errors)
