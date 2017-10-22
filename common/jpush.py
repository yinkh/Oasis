import jpush
from jpush.common import Unauthorized, APIConnectionException, JPushFailure

from .exception import PushError

import logging
logger = logging.getLogger("info")

app_key = u'5dc79b47ec6653db7233b149'
master_secret = u'd2a89afb0b1251ea19f7b0d5'

_jpush = jpush.JPush(app_key, master_secret)
_jpush.set_logging("DEBUG")


def audience(alias, title, msg_content, extras=None):
    push = _jpush.create_push()
    push.audience = jpush.audience(
        jpush.alias(alias),
    )
    push.message = jpush.message(msg_content, title=title, extras=extras)
    push.platform = jpush.all_
    try:
        response = push.send()
    except Unauthorized:
        raise PushError("Unauthorized", 1)
    except APIConnectionException:
        raise PushError("API Connection Error", 2)
    except JPushFailure as e:
        raise PushError('Push Error:{}'.format(e.details), e.error_code)
    except Exception as e:
        raise PushError("Exception:{}".format(str(e)), 3)


