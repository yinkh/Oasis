import logging

from datetime import datetime
from django.db import transaction
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from django.db.models import Q
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import UserRateThrottle

from common.permissions import IsSelf, IsFileOwnerOrReadOnly
from common.response import success_response, error_response
from common.viewset import ModelViewSet, CreateModelMixin, HumanizationSerializerErrorsMixin, GenericViewSet
from common.exception import VerifyError
from common.utils import get_list

from friend.models import Friend

from .serializers import *
from .filters import *
# from .signals import *
from .utils import *

logger = logging.getLogger("info")


# 检查短信验证码 验证通过后删除
# Receive ----------------------------------
# tel: 手机号码
# purpose: 验证码用途 1注册 2找回密码 3身份验证
# code: 验证码
# Return -----------------------------------
# 0 验证通过 1 验证码已超时 2 验证码错误 3 未发送验证码
def check_sms_verify(tel, purpose, code):
    # return True
    try:
        tel_verify = TelVerify.objects.get(tel=tel, purpose=purpose)
        if code == tel_verify.code:
            # 未过有效期
            if datetime.now() < (tel_verify.send_time + tel_verify.duration):
                # 验证通过
                tel_verify.delete()
            else:
                # 已过有效期 验证码已超时
                raise VerifyError('验证码已超时')
        else:
            # 验证码错误
            raise VerifyError('验证码错误')
    except ObjectDoesNotExist:
        # 未发送验证码
        raise VerifyError('未发送验证码')
    except MultipleObjectsReturned:
        TelVerify.objects.get(tel=tel, purpose=purpose).delete()
        raise VerifyError('验证码重复')


# 限制短信接口每60s可请求一次
class SmsRateThrottle(UserRateThrottle):
    scope = 'sms'


# 用户
class UserViewSet(ModelViewSet):
    queryset = User.objects.none()
    serializer_class = UserCreateSerializer
    serializer_classes = {
        'create': UserCreateSerializer,
        'list': UserListSerializer,
        'retrieve': UserSerializer,
        'update': UserModifySerializer,
    }
    # 403 错误均为未登录
    permission_classes = (IsAuthenticated,)
    filter_class = UserFilter
    ordering_fields = '__all__'
    search_fields = ('username', 'tel', 'nickname')

    # 重写 create 方法权限为AllowAny
    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [AllowAny, ]
        elif self.action in ('update', 'partial_update'):
            self.permission_classes = [IsAuthenticated, IsSelf, ]
        return super(self.__class__, self).get_permissions()

    def get_queryset(self):
        if self.request.user.is_authenticated:
            # 拉黑我的人
            black_list = Friend.objects.filter(to_user=self.request.user, is_block=True).all()
            # 不可见拉黑我的人
            return User.objects.exclude(id__in=[black.from_user.id for black in black_list])
        else:
            return self.queryset

    # override POST /user/
    # 用户注册
    # Receive ----------------------------------
    # username: 用户名 选填
    # tel: 手机号码
    # password: 密码
    # code: 验证码
    # Return -----------------------------------
    # 200 注册成功 400-1 数据格式错误 400-2 验证码验证不通过 400-3 手机号码不合法
    def create(self, request, *args, **kwargs):
        try:
            tel = request.data['tel']
            code = request.data['code']
            data = request.data.copy()
            if is_tel(tel):
                check_sms_verify(tel, 1, code)
                # 以手机号码注册
                serializer = UserCreateSerializer(data=data)
            else:
                return error_response(3, '请输入合法的手机号码')

            if serializer.is_valid():
                # 注册一个真实用户
                user = serializer.create(serializer.validated_data)
                user.refresh_im_token()
                data = {'id': user.id, 'token': user.get_token(), 'im_token': user.get_im_token(),
                        'name': user.get_full_name(), 'portal': request.build_absolute_uri(user.get_portrait())}
                return success_response(data)
            else:
                return error_response(1, self.humanize_errors(serializer))
        except VerifyError as e:
            return error_response(2, e.message)
        except KeyError as e:
            return error_response(1, '获取参数{}失败'.format(e.__context__))
        except Exception as e:
            return error_response(1, str(e))

    def destroy(self, request, *args, **kwargs):
        return success_response('禁止删除')

    # 用户登陆
    # Receive ----------------------------------
    # username: 用户名/手机号码
    # password: 密码
    # Return -----------------------------------
    # 200 登陆成功 400-1 数据格式错误 400-2 用户名或密码错误
    # 400-3 用户登陆凭证冲突 400-4 该账号未激活
    @list_route(methods=['POST'], permission_classes=[AllowAny])
    def login(self, request):
        try:
            username = request.data['username']
            try:
                instance = User.objects.get(Q(username=username) | Q(tel=username))
            except ObjectDoesNotExist:
                return error_response(2, '用户名或密码错误')
            except MultipleObjectsReturned:
                return error_response(3, '用户登陆凭证冲突')

            if 'password' in request.data:
                # 密码登陆
                user = authenticate(username=instance.username,
                                    password=request.data['password'])
            elif 'code' in request.data:
                # 验证码登陆
                if is_tel(username):
                    try:
                        check_sms_verify(username, 4, request.data['code'])
                        user = instance
                    except VerifyError as e:
                        return error_response(5, e.message)
                else:
                    return error_response(6, '请输入合法号码')
            else:
                return error_response(5, '未提供登陆凭证')

            if user is not None:
                if user.is_active:
                    # 登陆系统
                    login(request, user)
                    # 更新登陆时间
                    user.last_login = timezone.now()
                    user.save()
                    data = {'id': user.id, 'token': user.get_token(), 'im_token': user.get_im_token(),
                            'name': user.get_full_name(), 'portal': request.build_absolute_uri(user.get_portrait())}
                    return success_response(data)
                else:
                    return error_response(4, '该账号未激活')
            else:
                return error_response(2, '用户名或密码错误')
        except KeyError as e:
            return error_response(1, '获取参数{}失败'.format(e.__context__))
        except Exception as e:
            return error_response(1, str(e))

    # 用户退出登陆
    # Return -----------------------------------
    # 200 退出登陆成功
    @list_route(methods=['GET'])
    def logout(self, request):
        logout(request)
        return success_response('退出登陆成功')

    # 旧密码修改密码
    # Receive ----------------------------------
    # pwd_old: 新密码
    # pwd_new: 旧密码
    # Return -----------------------------------
    # 200 修改成功 400-1 数据格式错误 400-2 旧密码错误 400-3 该账号未激活
    @list_route(methods=['POST'])
    def change_pwd(self, request):
        try:
            user = authenticate(username=request.user.username,
                                password=request.data['pwd_old'])
            if user is not None:
                if user.is_active:
                    user.set_password(request.data['pwd_new'])
                    user.save()
                    return success_response('修改成功。')
                else:
                    return error_response(3, '该账号未激活')
            else:
                return error_response(2, '旧密码错误')
        except KeyError as e:
            return error_response(1, '获取参数{}失败'.format(e.__context__))
        except Exception as e:
            return error_response(1, str(e))

    # 找回密码
    # Receive ----------------------------------
    # tel: 手机号码
    # code: 验证码
    # pwd_new: 新密码
    # Return -----------------------------------
    # 200 修改成功 400-1 数据格式错误 400-2 无此用户 400-3 验证码验证不通过
    # 400-4 号码不合法 400-5 用户登陆凭证冲突 400-6 该账号未激活
    @list_route(methods=['POST'], permission_classes=[AllowAny])
    def find_pwd(self, request):
        try:
            tel = request.data['tel']
            code = request.data['code']
            # 防止输入空用户名试图登陆
            if not tel or tel == '':
                return error_response(2, '无此用户')

            if is_tel(tel):
                check_sms_verify(tel, 2, code)
                user = User.objects.get(tel=tel)
            else:
                return error_response(4, '请使用合法号码找回密码')

            if user.is_active:
                user.set_password(request.data['pwd_new'])
                user.save()
                return success_response('找回密码成功。')
            else:
                return error_response(6, '该账号未激活')
        except VerifyError as e:
            return error_response(3, e.message)
        except User.DoesNotExist:
            return error_response(2, '无此用户')
        except User.MultipleObjectsReturned:
            return error_response(5, '用户登陆凭证冲突')
        except KeyError as e:
            return error_response(1, '获取参数{}失败'.format(e.__context__))
        except Exception as e:
            return error_response(1, str(e))

    # 修改手机号码
    # Receive ----------------------------------
    # tel: 手机号码
    # code: 验证码
    # Return -----------------------------------
    # 200 修改成功 400-1 数据格式错误 400-2 验证码验证不通过
    # 400-3 号码不合法 400-4 该用户未激活 400-5 手机号码已被他人绑定
    @list_route(methods=['POST'])
    def change_tel(self, request):
        try:
            tel = request.data['tel']
            code = request.data['code']
            user = request.user

            if is_tel(tel):
                check_sms_verify(tel, 3, code)
                if user.is_active:
                    if User.objects.filter(tel=tel).exists():
                        return error_response(5, '该手机号码已被他人绑定')
                    user.tel = tel
                    user.save()
                    return success_response('修改成功')
                else:
                    return error_response(4, '该用户未激活')
            else:
                return error_response(3, '请输入合法号码')
        except VerifyError as e:
            return error_response(2, e.message)
        except KeyError as e:
            return error_response(1, '获取参数{}失败'.format(e.__context__))
        except Exception as e:
            return error_response(1, str(e))

    # 发送验证码
    # Receive ----------------------------------
    # tel: 手机号码
    # purpose : 验证码用途 1注册 2找回密码 3修改绑定 4身份验证
    # Return -----------------------------------
    # 200 发送成功 400-1 数据格式错误 400-2 该用户已注册,请直接登陆
    # 400-3 该用户未注册,无法找回密码  400-4 请输入合法号码 429 请求过快
    @list_route(methods=['POST'], permission_classes=[AllowAny], throttle_classes=[SmsRateThrottle])
    # @list_route(methods=['POST'], permission_classes=[AllowAny])
    def send_verify(self, request):
        try:
            purpose = int(request.data['purpose'])
            tel = request.data['tel']
            if is_tel(tel):
                if purpose == 1 and User.objects.filter(tel=tel).exists():
                    return error_response(2, '该用户已注册,请直接登陆')
                elif purpose == 2 and not User.objects.filter(tel=tel).exists():
                    return error_response(3, '该用户未注册,无法找回密码')

                # 发送短信验证码
                tel_verify, create = TelVerify.objects.get_or_create(tel=tel, purpose=purpose)
                # 未创建则更新
                if not create:
                    tel_verify.update()
                # 更新发送时间
                tel_verify.send_time = timezone.now()
                tel_verify.save()
                # 发送短信
                is_success, message = tel_verify.send_sms()
                if is_success:
                    return success_response('发送成功')
                else:
                    logger.error('短信发送失败 原因：{}'.format(message))
                    return error_response(5, message)
            else:
                return error_response(4, '请输入合法号码')
        except KeyError as e:
            return error_response(1, '获取参数{}失败'.format(e.__context__))
        except Exception as e:
            return error_response(1, str(e))

    # 刷新用户im_token
    # Return -----------------------------------
    # 200 新im_token 400-1 刷新失败
    @list_route(methods=['GET'])
    def refresh_im_token(self, request):
        if request.user.refresh_im_token():
            return success_response({'im_token': request.user.get_im_token()})
        else:
            return error_response(1, '刷新失败,请稍后再试。')

    # 查看用户是否存在
    # Receive ----------------------------------
    # username: 用户名/手机号码/电子邮箱
    # Return -----------------------------------
    # 200 true/false 400-1 数据格式错误
    @list_route(methods=['POST'], permission_classes=[AllowAny])
    def exist(self, request):
        try:
            username = request.data['username']
            User.objects.get(Q(username=username) |
                             Q(tel=username) |
                             Q(email=username))
            return success_response(True)
        except ObjectDoesNotExist:
            return success_response(False)
        except MultipleObjectsReturned:
            return success_response(False)
        except KeyError as e:
            return error_response(1, '获取参数{}失败'.format(e.__context__))
        except Exception as e:
            return error_response(1, str(e))

    # 查看当前OSS文件列表 测试用接口
    @list_route(methods=['GET'], permission_classes=[AllowAny])
    def oss(self, request):
        import oss2
        auth = oss2.Auth(settings.ACCESS_KEY_ID, settings.ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, settings.END_POINT, settings.BUCKET_NAME, enable_crc=False)
        file_list = [obj.key for obj in oss2.ObjectIterator(bucket, prefix='media')]
        return success_response(file_list)


# 文件
class FileViewSet(ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileListSerializer
    serializer_classes = {
        'create': FileModifySerializer,
        'list': FileListSerializer,
        'retrieve': FileSerializer,
        'update': FileModifySerializer,
    }
    permission_classes = (IsAuthenticated,)

    # 修改、删除需要所有者权限
    def get_permissions(self):
        if self.action in ('update', 'partial_update', 'destroy'):
            self.permission_classes = [IsAuthenticated, IsFileOwnerOrReadOnly, ]
        return super(self.__class__, self).get_permissions()

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            return serializer.save(user=self.request.user)
        else:
            return serializer.save()

    @list_route(methods=['POST'])
    @transaction.atomic
    def bulk_create(self, request):
        errors = []
        data = []
        sid = transaction.savepoint()
        for file in get_list(request.data, 'files'):
            serializer = FileModifySerializer(data={'file': file})
            if serializer.is_valid():
                instance = self.perform_create(serializer)
                data.append(FileInlineSerializer(instance, context=self.get_serializer_context()).data)
            else:
                errors.append(self.humanize_errors(serializer))
        if len(errors) == 0:
            transaction.savepoint_commit(sid)
            return success_response(data)
        else:
            transaction.savepoint_rollback(sid)
            return error_response(1, errors)


# 协议
class AgreementViewSet(CreateModelMixin, HumanizationSerializerErrorsMixin, GenericViewSet):
    queryset = Agreement.objects.all()
    serializer_class = AgreementCreateSerializer
    permission_classes = (IsAuthenticated,)

    # 创建协议
    # Receive ----------------------------------
    # is_agree: 是否授权协议
    # version: 协议版本
    # Return -----------------------------------
    # 200 设置成功 400-1 数据格式错误
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return success_response('设置成功')
        else:
            return error_response(1, self.humanize_errors(serializer))

    # 查看用户是否授权协议
    # Receive ----------------------------------
    # version: 协议版本
    # Return -----------------------------------
    # 200 true/false 400-1 数据格式错误
    @list_route(methods=['POST'])
    def check(self, request):
        try:
            instance = self.get_queryset().get(user=self.request.user, version=request.data['version'])
            return success_response(instance.is_agree)
        except ObjectDoesNotExist:
            return success_response(False)
        except MultipleObjectsReturned:
            return success_response(False)
        except KeyError as e:
            return error_response(1, '获取参数{}失败'.format(e.__context__))
        except Exception as e:
            return error_response(1, str(e))
