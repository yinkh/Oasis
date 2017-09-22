import re
import time
import random
from random import Random
from datetime import timedelta
from django.utils.translation import ngettext
from django.core.exceptions import ValidationError


def random_username(start_letter='Oasis_', random_length=20):
    """
    :param start_letter: 字符串起始字母
    :param random_length: 随机字符串长度
    :return: 随机生成的字符串
    """
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789-_'
    length = len(chars) - 1

    current_time = time.strftime('%Y%m%d%H%M%S')

    s = ''
    for i in range(random_length - 14 - len(start_letter)):
        s += chars[Random().randint(0, length)]
    if start_letter:
        return start_letter + s + current_time
    else:
        return str(s) + str(current_time)


def validate_tel(tel):
    """
    正则匹配手机号码
    :param tel: 手机号码
    :raise: ValidationError
    """
    # 删除+86字符
    tel = str(tel).replace('+86', '')
    tel_regex = re.compile('^0\d{2,3}\d{7,8}$|^1[358]\d{9}$|^147\d{8}')
    if not tel_regex.match(tel):
        raise ValidationError('请输入正确的手机号码。')


def validate_email(email):
    """
    正则匹配邮箱地址
    :param email: 邮箱地址
    :raise: ValidationError
    """
    # 格式 xx@xx.xx
    email_regex = re.compile('(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)')
    if not email_regex.match(email):
        raise ValidationError('请输入正确的邮箱地址。')


def is_tel(tel):
    """
    判断是否为手机号码
    :param tel: 手机号码
    :return: True False
    """
    # 删除+86字符
    tel = str(tel).replace('+86', '').replace(' ', '')
    tel_regex = re.compile('^0\d{2,3}\d{7,8}$|^1[358]\d{9}$|^147\d{8}')
    if tel_regex.match(tel):
        return True
    else:
        return False


def is_email(email):
    """
    判断是否为邮箱地址 格式 xx@xx.xx
    :param email: 邮箱地址
    :return: True False
    """
    #
    email_regex = re.compile('(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)')

    if not email or '@' not in email:
        return False

    if email_regex.match(email):
        return True
    else:
        return False


def localize_timedelta(delta):
    """
    时间段转换为对应语言的描述
    :param delta:
    :return:
    """
    ret = []
    num_years = int(delta.days / 365)
    if num_years > 0:
        delta -= timedelta(days=num_years * 365)
        ret.append(ngettext('%d year', '%d years', num_years) % num_years)

    if delta.days > 0:
        ret.append(ngettext('%d day', '%d days', delta.days) % delta.days)

    num_hours = int(delta.seconds / 3600)
    if num_hours > 0:
        delta -= timedelta(hours=num_hours)
        ret.append(ngettext('%d hour', '%d hours', num_hours) % num_hours)

    num_minutes = int(delta.seconds / 60)
    if num_minutes > 0:
        ret.append(ngettext('%d minute', '%d minutes', num_minutes) % num_minutes)

    return ' '.join(ret)