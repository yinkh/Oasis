from rest_framework.viewsets import GenericViewSet

from common.mixins import *


class ReadOnlyModelViewSet(RetrieveModelMixin,
                           ListModelMixin,
                           MultiSerializerMixin,
                           GenericViewSet):
    """
    A viewset that provides default `list()` and `retrieve()` actions.
    """
    pass


class ModelViewSet(CreateModelMixin,
                   RetrieveModelMixin,
                   UpdateModelMixin,
                   DestroyModelMixin,
                   ListModelMixin,
                   MultiSerializerMixin,
                   HumanizationSerializerErrorsMixin,
                   GenericViewSet):
    """
    A viewset that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` and `list()` actions.
    """
    pass
