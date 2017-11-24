from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import *


class UserTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='无论在前在后', password='123456', tel='18094213194')

    def test_user_create(self):
        """
        创建用户
        """
        url = reverse('user-list')
        tel_verify = TelVerify.objects.create(tel='17749503263', purpose=1)
        data = {'tel': tel_verify.tel, 'code': tel_verify.code, 'password': 'Oasis123456'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
