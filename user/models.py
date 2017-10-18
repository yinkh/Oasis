import os
import random
from datetime import timedelta

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import AbstractBaseUser, UserManager

from rest_framework_jwt.settings import api_settings

from common.models import Base
from common.utils import get_time_filename, send_sms, sizeof_fmt
from common.exception import SmsError

from rongcloud import RongCloud

# 融云实例
im = RongCloud(settings.IM_KEY, settings.IM_SECRET)


def get_portrait_path(instance, filename):
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
    # 手机号码
    tel = models.CharField(max_length=20,
                           unique=True,
                           error_messages={
                               'unique': "具有该手机号码的用户已存在",
                           },
                           verbose_name=u'手机号码')
    # 头像
    portrait = models.ForeignKey('user.File',
                                 related_name='user_portrait',
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
    # 昵称
    nickname = models.CharField(max_length=30,
                                blank=True,
                                verbose_name=u'昵称')
    # 生日
    birth_day = models.DateField(null=True,
                                 blank=True,
                                 verbose_name=u'生日')
    # 电子邮件
    email = models.EmailField(max_length=255,
                              blank=True,
                              verbose_name=u'电子邮件')
    # 所在地
    location = models.CharField(max_length=255,
                                blank=True,
                                verbose_name=u'所在地')
    # 个人简介
    introduction = models.TextField(blank=True,
                                    verbose_name=u'个人简介')
    # 融云IM Token
    im_token = models.TextField(null=True,
                                blank=True,
                                verbose_name=u'融云IM Token')
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

    # 获取全名
    def get_full_name(self):
        if self.nickname == '':
            return self.username
        else:
            return self.nickname

    get_full_name.short_description = '全名'

    # 获取名称
    def get_short_name(self):
        return self.nickname

    # 获取头像
    def get_portrait(self):
        if self.portrait:
            return self.portrait.file.url
        else:
            if self.gender == 0:
                return '/static/default/user/default_female.png'
            elif self.gender == 1:
                return '/static/default/user/default_male.png'
            else:
                return '/static/default/user/default.png'

    # 获取Token
    def get_token(self):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(self)
        token = jwt_encode_handler(payload)
        return token

    def get_im_token(self):
        if self.im_token:
            return self.im_token
        else:
            self.refresh_im_token()
            return self.im_token

    def refresh_im_token(self):
        """
        获取IM Token  用user_id作为注册融云的id
        :return: True/False
        """
        # API更新后调用.get()方法后获取到的才是返回的dict
        result = im.User.getToken(self.id, self.username, self.get_portrait()).result
        if 'code' in result and result['code'] == 200:
            if 'token' in result:
                self.im_token = result['token']
                self.save()
                return True
        return False

    def operate_black_list(self, user_id, operate):
        """
        拉黑/取消拉黑
        :param user_id: 待拉黑/取消拉黑用户ID
        :param operate: add 拉黑 remove取消拉黑
        :return: True 操作成功 False 操作失败
        """
        if operate == 'add':
            result = im.User.addBlacklist(self.id, user_id).result
        elif operate == 'remove':
            result = im.User.removeBlacklist(self.id, user_id).result
        else:
            result = None
        if result and 'code' in result and result['code'] == 200:
            return True
        else:
            return False

    def __str__(self):
        return '{} {}'.format(self.id, self.get_full_name())


# 短信验证码
class TelVerify(models.Model):
    # 手机号码
    tel = models.CharField(max_length=12,
                           verbose_name=u'手机号码')
    # 验证码
    code = models.CharField(max_length=30,
                            verbose_name=u'验证码')
    PURPOSE = {
        1: u'用户注册',
        2: u'找回密码',
        3: u'修改绑定',
        4: u'身份验证',
    }
    # 验证码用途 1注册 2找回密码 3修改绑定 4身份验证
    purpose = models.IntegerField(default=1,
                                  choices=PURPOSE.items(),
                                  verbose_name=u'用途')
    # 有效时长
    duration = models.DurationField(default=timedelta(minutes=15),
                                    verbose_name='有效时长')
    # 发送时间
    send_time = models.DateTimeField(default=timezone.now,
                                     verbose_name=u'发送时间')
    # 是否发送成功
    is_success = models.BooleanField(default=False,
                                     verbose_name=u'是否发送成功')
    # 失败原因
    failure_reason = models.CharField(max_length=255,
                                      null=True,
                                      blank=True,
                                      verbose_name=u'失败原因')
    # 创建时间
    create_time = models.DateTimeField(auto_now_add=True,
                                       verbose_name=u'创建时间')
    # 更新时间
    update_time = models.DateTimeField(auto_now=True,
                                       verbose_name=u'更新时间')

    class Meta:
        verbose_name = '短信验证码'
        verbose_name_plural = '短信验证码'
        ordering = ('id',)
        unique_together = ('tel', 'purpose')

    def save(self, *args, **kwargs):
        if not self.pk:
            self.code = self.generate_verification_code()
        return super(TelVerify, self).save(*args, **kwargs)

    # 更新验证码
    def update(self):
        self.code = self.generate_verification_code()
        self.save()
        return self.code

    # 阿里大于发送短信
    def send_sms(self):
        try:
            if self.purpose == 1:
                # 用户注册
                send_sms(self.tel, 'SMS_98365026', {'code': self.code})
            elif self.purpose == 2:
                # 找回密码
                send_sms(self.tel, 'SMS_98365026', {'code': self.code})
            elif self.purpose == 3:
                # 修改绑定
                send_sms(self.tel, 'SMS_98365026', {'code': self.code})
            else:
                # 身份验证
                send_sms(self.tel, 'SMS_98365026', {'code': self.code})
            self.is_success = True
            self.failure_reason = ''
            self.save()
            return True, None
        except SmsError as e:
            self.is_success = False
            self.failure_reason = e.message
            self.save()
            return False, e.message

    @staticmethod
    def generate_verification_code():
        """
        :return: 随机生成6位的验证码
        """
        code_list = []
        # 0-9数字
        for i in range(10):
            code_list.append(str(i))
        # 从list中随机获取6个元素，作为一个片断返回
        my_slice = random.sample(code_list, 6)
        # list to string
        verification_code = ''.join(my_slice)
        return verification_code

    def __str__(self):
        return self.tel


def get_file_path(instance, filename):
    return 'file/{}'.format(get_time_filename(filename))


# 文件
class File(models.Model):
    # 上传人
    user = models.ForeignKey('user.User',
                             related_name='file_user',
                             null=True,
                             blank=True,
                             verbose_name=u'上传人')
    # 文件
    file = models.FileField(upload_to=get_file_path,
                            verbose_name=u'文件')
    # 文件名
    filename = models.CharField(max_length=255,
                                blank=True,
                                verbose_name=u'文件名')
    # 文件格式
    ext = models.CharField(max_length=255,
                           blank=True,
                           verbose_name=u'文件格式')
    # 文件大小
    size = models.CharField(max_length=255,
                            blank=True,
                            verbose_name=u'文件大小')
    # 创建时间
    create_time = models.DateTimeField(auto_now_add=True,
                                       verbose_name=u'创建时间')
    # 更新时间
    update_time = models.DateTimeField(auto_now=True,
                                       verbose_name=u'更新时间')

    class Meta:
        verbose_name = '文件'
        verbose_name_plural = '文件'
        ordering = ('-id',)

    def save(self, *args, **kwargs):
        if not self.id:
            self.set_info()
        else:
            # 改
            this = File.objects.get(id=self.id)
            if this.file != self.file:
                this.file.delete(save=False)
                self.set_info()
        return super(File, self).save(*args, **kwargs)

    def set_info(self):
        filename = self.file.name
        self.filename = filename
        ext = os.path.splitext(filename)[1][1:]
        self.ext = ext
        self.size = sizeof_fmt(self.file.size)

    def __str__(self):
        return self.filename


# 协议
class Agreement(Base):
    # 用户
    user = models.ForeignKey('user.User',
                             on_delete=models.CASCADE,
                             related_name='agreement_user',
                             verbose_name=u'用户')
    # 版本
    version = models.CharField(max_length=255,
                               verbose_name=u'版本')
    # 是否授权
    is_agree = models.BooleanField(default=False,
                                   verbose_name=u'是否授权')

    class Meta:
        verbose_name = '协议'
        verbose_name_plural = '协议'
        ordering = ('id',)

    def __str__(self):
        return '{} version:{} is_agree:{}'.format(self.user.get_full_name(), self.version, self.is_agree)
