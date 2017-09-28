import uuid
import datetime
import hmac
import base64
import requests
from urllib.parse import quote

from django.conf import settings


class Singleton(type):
    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(name, bases, dict)
        cls.instance = None

    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kw)
        return cls.instance


class AliYunSMS(metaclass=Singleton):
    def __init__(self):
        self.format = "JSON"
        self.version = "2017-05-25"
        self.key = settings.SMS_ID
        self.secret = settings.SMS_SECRET
        self.signature = ""
        self.signature_method = "HMAC-SHA1"
        self.signature_version = "1.0"
        self.region_id = "cn-hangzhou"  # 区域,可选

        self.gateway = "http://dysmsapi.aliyuncs.com/"
        self.action = ""
        self.sign = ""
        self.template = ""
        self.params = {}
        self.phone = None

    def send_single(self, phone, sign, template, params):
        self.action = "SendSms"
        self.phone = phone
        self.sign = sign
        self.params = params
        self.template = template

        query_string = self.build_query_string()

        resp = requests.get(self.gateway + "?" + query_string)
        return resp

    def build_query_string(self):
        query = []
        query.append(("Format", self.format))
        query.append(("Version", self.version))
        query.append(("AccessKeyId", self.key))
        query.append(("SignatureMethod", self.signature_method))
        query.append(("SignatureVersion", self.signature_version))
        query.append(("SignatureNonce", str(uuid.uuid4())))
        query.append(("Timestamp", datetime.datetime.utcnow().isoformat("T")))
        query.append(("RegionId", self.region_id))
        query.append(("Action", self.action))
        query.append(("SignName", self.sign))
        query.append(("TemplateCode", self.template))
        query.append(("PhoneNumbers", self.phone))
        params = "{"
        for param in self.params:
            params += "\"" + param + "\"" + ":" + "\"" + str(self.params[param]) + "\"" + ","
        params = params[:-1] + "}"
        query.append(("TemplateParam", params))
        query = sorted(query, key=lambda key: key[0])
        query_string = ""
        for item in query:
            query_string += quote(item[0], safe="~") + "=" + quote(item[1], safe="~") + "&"
        query_string = query_string[:-1]
        tosign = "GET&%2F&" + quote(query_string, safe="~")
        secret = self.secret + "&"
        hmb = hmac.new(secret.encode("utf-8"), tosign.encode("utf-8"), "sha1").digest()
        self.signature = quote(base64.standard_b64encode(hmb).decode("ascii"), safe="~")
        query_string += "&" + "Signature=" + self.signature
        return query_string
