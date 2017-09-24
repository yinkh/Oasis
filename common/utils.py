import os
from datetime import datetime


def get_time_filename(filename):
    """
    将文件名修改为 年月日-时分秒-毫秒 格式
    :param filename: 原文件名
    :return: 年月日-时分秒-毫秒
    """
    # 文件拓展名
    ext = os.path.splitext(filename)[1]
    # 文件目录
    d = os.path.dirname(filename)
    # 自定义文件名,年月日-时分秒-毫秒
    current_time = datetime.now().strftime('%Y%m%d-%H%M%S-%f')[:-3]
    # 合成文件名
    filename = os.path.join(d, current_time + ext)
    return filename


def isdigit(string):
    """
    :param string:
    :return: 该字符是否是数字
    """
    if isinstance(string, int):
        return True
    else:
        return isinstance(string, str) and string.isdigit()


_true_set = {'yes', 'true', 't', 'y', '1'}
_false_set = {'no', 'false', 'f', 'n', '0'}


def str2bool(value, raise_exc=False):
    """
    str转bool
    :param value: 值
    :param raise_exc: 是否抛出异常
    :return: 转换后的值或者None
    """
    value = value.lower()
    if value in _true_set:
        return True
    if value in _false_set:
        return False
    if raise_exc:
        raise ValueError('Expected "%s"' % '", "'.join(_true_set | _false_set))
    return None


def str2bool_exc(value):
    """
    str转bool 抛出异常
    :param value: value: 值
    :return:转换后的值或者ValueError
    """
    return str2bool(value, raise_exc=True)