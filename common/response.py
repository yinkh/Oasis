from rest_framework.response import Response
from rest_framework import status
import logging
logger = logging.getLogger("info")


def success_response(data):
    """
    成功时返回 200-code
    :param data:
    :return:
    """
    if isinstance(data, dict):
        return Response(data=data, status=status.HTTP_200_OK)
    else:
        return Response(data={'data': data}, status=status.HTTP_200_OK)


def error_response(code, data):
    """
    错误时返回 400-code
    :param code: 自定义错误码
    :param data: 错误详情
    :return: Response
    """
    logger.error("code: %d, data: %s" % (code, data))
    return Response(data={'code': code, 'data': data}, status=status.HTTP_400_BAD_REQUEST)

