import random
import apns
from threading import Event

from gcm import GCM
from gcm.gcm import (
    GCMNotRegisteredException,
    GCMException
)

from django.conf import settings

from models import Device
from exceptions import (
    PushException,
    PushGCMApiKeyException,
    PushAPNsCertificateException
)

dispatchers_cache = {}


class Dispatcher(object):
    PUSH_RESULT_SENT = 1
    PUSH_RESULT_NOT_REGISTERED = 2
    PUSH_RESULT_EXCEPTION = 3

    def send(self, device_key, data):
        raise NotImplemented()


class APNSDispatcher(Dispatcher):

    connection = None

    error_response_events = None

    STATUS_CODE_NO_ERROR = 0

    STATUS_CODE_PROCESSING_ERROR = 1

    STATUS_CODE_MISSING_DEVICE_TOKEN = 2

    STATUS_CODE_MISSING_TOPIC = 3

    STATUS_CODE_MISSING_PAYLOAD = 4

    STATUS_CODE_INVALID_TOKEN_SIZE = 5

    STATUS_CODE_INVALID_TOPIC_SIZE = 6

    STATUS_CODE_INVALID_PAYLOAD_SIZE = 7

    STATUS_CODE_INVALID_TOKEN = 8

    STATUS_CODE_SHUTDOWN = 10

    STATUS_CODE_UNKNOWN = 255

    class ErrorResponseEvent(object):

        _status = 0

        _event = None

        def __init__(self):
            self._event = Event()

        def set_status(self, value):
            self._status = value

            self._event.set()

        def wait_for_response(self, timeout):
            self._event.wait(timeout)

            return self._status

    def __init__(self):
        super(APNSDispatcher, self).__init__()

        self.error_response_events = {}

    @property
    def cert_file(self):
        return getattr(settings, 'PUSHY_APNS_CERTIFICATE_FILE', None)

    @property
    def key_file(self):
        return getattr(settings, 'PUSHY_APNS_KEY_FILE', None)

    @property
    def use_sandbox(self):
        return bool(getattr(settings, 'PUSHY_APNS_SANDBOX', False))

    def on_error_response(self, error_response):
        status = error_response['status']
        identifier = error_response['identifier']

        event_object = self.error_response_events.pop(identifier, None)

        if event_object:
            event_object.set_status(status)

    def establish_connection(self):
        if self.cert_file is None:
            raise PushAPNsCertificateException

        connection = apns.APNs(
            use_sandbox=self.use_sandbox,
            cert_file=self.cert_file,
            key_file=self.key_file,
            enhanced=True
        )

        connection.gateway_server.register_response_listener(
            self.on_error_response
        )

        self.connection = connection

    @staticmethod
    def create_identifier():
        return random.getrandbits(32)

    def _send_notification(self, token, payload):
        identifier = self.create_identifier()

        event_object = self.ErrorResponseEvent()

        self.error_response_events[identifier] = event_object

        self.connection.gateway_server.send_notification(
            token, payload, identifier=identifier
        )

        return event_object

    def send(self, device_key, data):
        if not self.connection:
            self.establish_connection()

        payload = apns.Payload(
            alert=data.pop('alert', None),
            sound=data.pop('sound', None),
            badge=data.pop('badge', None),
            category=data.pop('category', None),
            content_available=bool(data.pop('content-available', False)),
            custom=data or {}
        )

        event = self._send_notification(device_key, payload)

        status = event.wait_for_response(1.5)

        if status in (self.STATUS_CODE_INVALID_TOKEN,
                      self.STATUS_CODE_INVALID_TOKEN_SIZE):
            push_result = self.PUSH_RESULT_NOT_REGISTERED
        elif status == self.STATUS_CODE_NO_ERROR:
            push_result = self.PUSH_RESULT_SENT
        else:
            push_result = self.PUSH_RESULT_EXCEPTION

        return push_result, 0


class GCMDispatcher(Dispatcher):

    def _send_plaintext(self, gcm_client, device_key, data):
        return gcm_client.plaintext_request(device_key, data=data)

    def _send_json(self, gcm_client, device_key, data):
        response = gcm_client.json_request([device_key], data=data)

        device_error = None

        if 'errors' in response:
            for error, reg_ids in response['errors'].items():
                # Check for errors and act accordingly

                if device_key in reg_ids:
                    device_error = error
                    break

        if device_error:
            gcm_client.raise_error(device_error)

            raise GCMException(device_error)

        if 'canonical' in response:
            canonical_id = response['canonical'].get(device_key, 0)
        else:
            canonical_id = 0

        return canonical_id

    def send(self, device_key, data):
        gcm_api_key = getattr(settings, 'PUSHY_GCM_API_KEY', None)

        gcm_json_payload = getattr(settings, 'PUSHY_GCM_JSON_PAYLOAD', True)

        if not gcm_api_key:
            raise PushGCMApiKeyException()

        gcm = GCM(gcm_api_key)

        # Plaintext request
        try:
            if gcm_json_payload:
                canonical_id = self._send_json(gcm, device_key, data)
            else:
                canonical_id = self._send_plaintext(gcm, device_key, data)

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
