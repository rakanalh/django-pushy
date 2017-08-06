from django.conf import settings
from pushjack import (
    APNSClient,
    APNSSandboxClient,
    GCMClient
)
from pushjack.exceptions import (
    GCMAuthError,
    GCMMissingRegistrationError,
    GCMInvalidRegistrationError,
    GCMUnregisteredDeviceError,
    GCMInvalidPackageNameError,
    GCMMismatchedSenderError,
    GCMMessageTooBigError,
    GCMInvalidDataKeyError,
    GCMInvalidTimeToLiveError,
    GCMTimeoutError,
    GCMInternalServerError,
    GCMDeviceMessageRateExceededError,

    APNSAuthError,
    APNSProcessingError,
    APNSMissingTokenError,
    APNSMissingTopicError,
    APNSMissingPayloadError,
    APNSInvalidTokenSizeError,
    APNSInvalidTopicSizeError,
    APNSInvalidPayloadSizeError,
    APNSInvalidTokenError,
    APNSShutdownError,
    APNSUnknownError
)

from .models import Device
from .exceptions import (
    PushAuthException,
    PushInvalidTokenException,
    PushInvalidDataException,
    PushServerException
)

dispatchers_cache = {}


class Dispatcher(object):
    def send(self, device_key, data):
        raise NotImplementedError()


class APNSDispatcher(Dispatcher):
    def __init__(self):
        super(APNSDispatcher, self).__init__()
        self._client = None

    @property
    def cert_file(self):
        return getattr(settings, 'PUSHY_APNS_CERTIFICATE_FILE', None)

    @property
    def use_sandbox(self):
        return bool(getattr(settings, 'PUSHY_APNS_SANDBOX', False))

    def establish_connection(self):
        if self.cert_file is None:
            raise PushAuthException('Missing APNS certificate error')

        target_class = APNSClient
        if self.use_sandbox:
            target_class = APNSSandboxClient

        self._client = target_class(
            certificate=self.cert_file,
            default_error_timeout=10,
            default_expiration_offset=2592000,
            default_batch_size=100
        )

    def _send(self, token, payload):
        try:
            response = self._client.send(
                [token],
                title=payload.pop('title', None),
                message=payload.pop('message', None),
                sound=payload.pop('sound', None),
                badge=payload.pop('badge', None),
                category=payload.pop('category', None),
                content_available=True,
                extra=payload or {}
            )

            if response.errors:
                raise response.errors.pop()
            return None

        except APNSAuthError:
            raise PushAuthException()

        except (APNSMissingTokenError,
                APNSInvalidTokenError):
            raise PushInvalidTokenException()

        except (APNSProcessingError,
                APNSMissingTopicError,
                APNSMissingPayloadError,
                APNSInvalidTokenSizeError,
                APNSInvalidTopicSizeError,
                APNSInvalidPayloadSizeError):
            raise PushInvalidDataException()

        except (APNSShutdownError,
                APNSUnknownError):
            raise PushServerException()

    def send(self, device_key, payload):
        if not self._client:
            self.establish_connection()

        return self._send(device_key, payload)


class GCMDispatcher(Dispatcher):
    def __init__(self, api_key=None):
        if not api_key:
            api_key = getattr(settings, 'PUSHY_GCM_API_KEY', None)
        self._api_key = api_key

    def _send(self, device_key, payload):
        if not self._api_key:
            raise PushAuthException()

        gcm_client = GCMClient(self._api_key)
        try:
            response = gcm_client.send(
                [device_key],
                payload
            )

            if response.errors:
                raise response.errors.pop()

            canonical_id = None
            if response.canonical_ids:
                canonical_id = response.canonical_ids[0].new_id
            return canonical_id

        except GCMAuthError:
            raise PushAuthException()

        except (GCMMissingRegistrationError,
                GCMInvalidRegistrationError,
                GCMUnregisteredDeviceError):
            raise PushInvalidTokenException()

        except (GCMInvalidPackageNameError,
                GCMMismatchedSenderError,
                GCMMessageTooBigError,
                GCMInvalidDataKeyError,
                GCMInvalidTimeToLiveError):
            raise PushInvalidDataException()

        except (GCMTimeoutError,
                GCMInternalServerError,
                GCMDeviceMessageRateExceededError):
            raise PushServerException()

    def send(self, device_key, payload):
        return self._send(device_key, payload)


def get_dispatcher(device_type):
    if device_type in dispatchers_cache and dispatchers_cache[device_type]:
        return dispatchers_cache[device_type]

    if device_type == Device.DEVICE_TYPE_ANDROID:
        dispatchers_cache[device_type] = GCMDispatcher()
    else:
        dispatchers_cache[device_type] = APNSDispatcher()

    return dispatchers_cache[device_type]
