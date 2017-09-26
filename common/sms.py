import uuid
import datetime
import hmac
import base64
import requests
from urllib.parse import quote

# ACCESS_KEY_ID/ACCESS_KEY_SECRET 根据实际申请的账号信息进行替换
ACCESS_KEY_ID = "LTAICBBycK9mbE9g"

ACCESS_KEY_SECRET = "ohU9KJnc17E8QpRyzK9QTY7i5s2Qxj"


class AliYunSMS(object):
    def __init__(self):
        self.format = "JSON"
        self.version = "2017-05-25"
        self.key = ACCESS_KEY_ID
        self.secret = ACCESS_KEY_SECRET
        self.signature = ""
        self.signature_method = "HMAC-SHA1"
        self.signature_version = "1.0"
        self.signature_nonce = str(uuid.uuid4())
        self.timestamp = datetime.datetime.utcnow().isoformat("T")
        self.region_id = ALIYUN_API_REGION_ID

        self.gateway = ALISMS_GATEWAY
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
        resp = resp.json()
        return resp

    def build_query_string(self):
        query = []
        query.append(("Format", self.format))
        query.append(("Version", self.version))
        query.append(("AccessKeyId", self.key))
        query.append(("SignatureMethod", self.signature_method))
        query.append(("SignatureVersion", self.signature_version))
        query.append(("SignatureNonce", self.signature_nonce))
        query.append(("Timestamp", self.timestamp))
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


# 可选XML
ALIYUN_API_FORMAT = "JSON"

# 区域,可选
ALIYUN_API_REGION_ID = "cn-hangzhou"

ALISMS_GATEWAY = "http://dysmsapi.aliyuncs.com/"
ALISMS_SIGN = "Oasis绿洲"
ALISMS_TPL_REGISTER = "SMS_98365026"

sms = AliYunSMS()
# :param phone: 手机号
# :param sign: 短信签名
# :param template: 短信模板
# :param params: 模板变量
# sms.send_singe(phone, sign, template, params)

# TODO 调用短信记录查询接口，返回json
response = sms.send_single("18094213193", ALISMS_SIGN, ALISMS_TPL_REGISTER, {"code": "12345"})
print(response)