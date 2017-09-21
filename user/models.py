from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import AbstractBaseUser, UserManager

from common.utils import get_time_filename


def get_file_path(instance, filename):
    return 'user/{}'.format(get_time_filename(filename))


# 用户
class User(AbstractBaseUser, PermissionsMixin):
    # 用户名
    username = models.CharField(
        max_length=150,
        null=True,
        unique=True,
        help_text='用户名仅可包含字母、数字、-、_，但不可为纯数字。',
        validators=[RegexValidator(
            regex='^(?![0-9]*$)[-_\w]*$',
            message='用户名仅可包含字母、数字、-、_，但不可为纯数字。',
            code='invalid_username'
        )],
        error_messages={
            'unique': "该用户名已被注册",
        },
        verbose_name=u'用户名'
    )
    # 头像
    portrait = models.ImageField(upload_to=get_file_path,
                                 null=True,
                                 blank=True,
                                 verbose_name=u'头像')
    # 性别 必选
    GENDER = {
        0: u'女',
        1: u'男',
        2: u'保密',
    }
    gender = models.IntegerField(choices=GENDER.items(),
                                 default=2,
                                 blank=True,
                                 verbose_name=u'性别')
    # 姓名
    name = models.CharField(max_length=30,
                            blank=True,
                            verbose_name=u'姓名')
    # 生日
    birth_day = models.DateField(null=True,
                                 blank=True,
                                 verbose_name=u'生日')
    # 电子邮件
    email = models.CharField(max_length=255,
                             unique=True,
                             null=True,
                             blank=True,
                             verbose_name=u'电子邮件')
    # 手机号码
    tel = models.CharField(max_length=20,
                           unique=True,
                           null=True,
                           blank=True,
                           error_messages={
                               'unique': "具有该手机号码的用户已存在",
                           },
                           verbose_name=u'手机号码')
    # 所在地
    location = models.CharField(max_length=255,
                                blank=True,
                                verbose_name=u'所在地')
    # 个人简介
    introduction = models.TextField(blank=True,
                                    verbose_name=u'个人简介')
    # 控制该用户是否可以登录admin site
    is_staff = models.BooleanField(_('staff status'),
                                   default=False, )
    # 反选既等同于删除用户
    is_active = models.BooleanField(_('active'),
                                    default=True, )
    # 账号创建时间
    date_joined = models.DateTimeField(_('date joined'),
                                       blank=True,
                                       default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('用户')
        verbose_name_plural = _('用户')
        ordering = ('id',)

        permissions = (
            ("view_user", "查看用户"),
            ("add_settings", "新增设置"),
            ("change_settings", "更改设置"),
            ("delete_settings", "删除设置"),
        )

    # 获取全名
    def get_full_name(self):
        if self.name == '':
            return self.username
        else:
            return self.name

    get_full_name.short_description = '全名'

    # 获取名称
    def get_short_name(self):
        return self.name

    def get_portrait(self):
        if self.portrait:
            return self.portrait.url
        else:
            if self.gender == 0:
                return '/media/default/user/default_female.png'
            elif self.gender == 1:
                return '/media/default/user/default_male.png'
            else:
                return '/media/default/user/default.png'

    def __str__(self):
        return '{} {}'.format(self.id, self.get_full_name())
