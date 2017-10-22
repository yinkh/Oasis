from django.contrib.auth import password_validation
from django.contrib.auth.hashers import make_password

from common.serializers import *
from common.utils import validate_image_ext, sizeof_fmt
from friend.models import Friend
from .models import *
from .utils import random_username, is_tel


# --------------------------------- 用户 ---------------------------------
# 创建用户
class UserCreateSerializer(ModelSerializer):
    def create(self, validated_data):
        if 'username' in validated_data:
            username = validated_data['username']
        else:
            username = random_username()
        # 使用create_user不是create
        instance = User.objects.create_user(username=username,
                                            tel=validated_data['tel'],
                                            password=validated_data['password'])
        return instance

    def validate_password(self, value):
        # 验证密码格式
        password_validation.validate_password(value)
        return value

    class Meta:
        model = User
        fields = ('username', 'tel', 'password')
        extra_kwargs = {'username': {'required': False}}


# 用户信息
class UserExpandSerializer(ModelSerializer):
    password = serializers.CharField(max_length=128, required=False)

    def validate_password(self, value):
        if 'action' in self.context:
            if self.context['action'] == 'update':
                # 验证密码格式
                password_validation.validate_password(value)
                # 重新生成密码
                value = make_password(value)
        return value

    # 设置tel
    def validate_tel(self, value):
        if is_tel(value):
            return value
        else:
            raise serializers.ValidationError("请输入正确的手机号码")

    def create(self, validated_data):
        if 'username' in validated_data:
            username = validated_data.pop('username')
        else:
            username = random_username()

        user = User.objects.create_user(username=username, **validated_data)
        return user

    class Meta:
        model = User
        fields = ('username', 'password', 'gender', 'nickname', 'birth_day', 'email',
                  'tel', 'fixed_tel', 'qq', 'we_chat', 'contact_address',)
        extra_kwargs = {'username': {'required': False}}


# 列表用户
class UserListSerializer(ModelSerializer):
    portrait = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'portrait', 'gender', 'get_gender_display', 'full_name')

    def get_portrait(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_portrait())

    def get_full_name(self, instance):
        request = self.context['request']
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                friend = Friend.objects.get(from_user=request.user, to_user=instance)
                return friend.remark
            except (Friend.DoesNotExist, Friend.MultipleObjectsReturned):
                pass
        return instance.get_full_name()


# 全部信息
class UserSerializer(ModelSerializer):
    portrait = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'tel', 'portrait', 'gender', 'nickname', 'birth_day', 'email',
                  'location', 'introduction', 'last_login', 'get_gender_display', 'full_name')

    def get_portrait(self, instance):
        request = self.context.get('request')
        return request.build_absolute_uri(instance.get_portrait())

    def get_full_name(self, instance):
        request = self.context['request']
        if hasattr(request, 'user') and request.user.is_authenticated:
            instance.get_full_name(user=request.user)
        return instance.get_full_name()


# 全部信息
class UserModifySerializer(ModelSerializer):
    def validate_portrait(self, data):
        if data:
            if not validate_image_ext(data.ext):
                raise serializers.ValidationError('非法的图片类型')
            if data.file.size > settings.MAX_IMAGE_SIZE:
                raise serializers.ValidationError('文件 {} 大小超过{}'.format(data.filename,
                                                                        sizeof_fmt(settings.MAX_IMAGE_SIZE)))
            request = self.context['request']
            if data.user and hasattr(request, 'user'):
                if data.user != request.user:
                    raise serializers.ValidationError('仅可使用本人上传或者公开图片')
        return data

    class Meta:
        model = User
        fields = ('username', 'portrait', 'gender', 'nickname', 'birth_day', 'email', 'location', 'introduction')


# --------------------------------- 文件 ---------------------------------
# 创建\修改文件
class FileModifySerializer(ModelSerializer):
    class Meta:
        model = File
        fields = ('file',)


# 列表文件
class FileListSerializer(ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'


# 文件详情
class FileSerializer(ModelSerializer):
    user = UserListSerializer(read_only=True)

    class Meta:
        model = File
        fields = '__all__'


# 文件-级联显示
class FileInlineSerializer(ModelSerializer):
    class Meta:
        model = File
        fields = ('id', 'file', 'filename', 'ext', 'size')


# --------------------------------- 协议 ---------------------------------
# 创建协议
class AgreementCreateSerializer(ModelSerializer):
    def create(self, validated_data):
        instance, is_created = Agreement.objects.get_or_create(user=validated_data['user'],
                                                               version=validated_data['version'])
        instance.is_agree = validated_data['is_agree']
        instance.save()
        return instance

    class Meta:
        model = Agreement
        fields = ('user', 'version', 'is_agree')
