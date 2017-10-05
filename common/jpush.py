import jpush
from jpush.common import Unauthorized, APIConnectionException, JPushFailure

app_key = u'5dc79b47ec6653db7233b149'
master_secret = u'd2a89afb0b1251ea19f7b0d5'

_jpush = jpush.JPush(app_key, master_secret)
_jpush.set_logging("DEBUG")

push = _jpush.create_push()


def push(alias, alert):
    push.audience = jpush.audience(
        jpush.alias(alias),
    )
    push.notification = jpush.notification(alert=alert)
    push.platform = jpush.all_
    try:
        response = push.send()
        print(response)
    except (Unauthorized, APIConnectionException, JPushFailure) as e:
        print(str(e))
    except Exception as e:
        print(str(e))
