from gcm import GCM
from gcm.gcm import GCMNotRegisteredException

from django.conf import settings

from models import Device
from exceptions import PushException, PushGCMApiKeyException

dispatchers_cache = {}


class Dispatcher(object):
    PUSH_RESULT_SENT = 1
    PUSH_RESULT_NOT_REGISTERED = 2
    PUSH_RESULT_EXCEPTION = 3

    def send(self, device_key, data):
        raise NotImplemented()


class APNSDispatcher(Dispatcher):
    def send(self, device_key, data):
        pass


class GCMDispatcher(Dispatcher):
    def send(self, device_key, data):
        gcm_api_key = getattr(settings, 'PUSHY_GCM_API_KEY', None)
        if not gcm_api_key:
            raise PushGCMApiKeyException()

        gcm = GCM(gcm_api_key)

        # Plaintext request
        try:
            canonical_id = gcm.plaintext_request(registration_id=device_key,
                                                 data=data)
            if canonical_id:
                return self.PUSH_RESULT_SENT, canonical_id
            else:
                return self.PUSH_RESULT_SENT, 0
        except GCMNotRegisteredException:
            return self.PUSH_RESULT_NOT_REGISTERED, 0
        except IOError:
            return self.PUSH_RESULT_EXCEPTION, 0
        except PushException:
            return self.PUSH_RESULT_EXCEPTION, 0


def get_dispatcher(device_type):
    if device_type in dispatchers_cache and dispatchers_cache[device_type]:
        return dispatchers_cache[device_type]

    if device_type == Device.DEVICE_TYPE_ANDROID:
        dispatchers_cache[device_type] = GCMDispatcher()
    elif device_type == Device.DEVICE_TYPE_IOS:
        dispatchers_cache[device_type] = APNSDispatcher()

    return dispatchers_cache[device_type]
