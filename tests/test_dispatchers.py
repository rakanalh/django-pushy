from django.test.utils import override_settings
import mock
from gcm.gcm import GCMNotRegisteredException

from django.test import TestCase

from pushy.exceptions import PushException, PushGCMApiKeyException, PushAPNsCertificateException

from pushy.models import Device
from pushy import dispatchers


class DispatchersTestCase(TestCase):

    def test_check_cache(self):
        dispatchers.dispatchers_cache = {}

        # Test cache Android
        dispatcher1 = dispatchers.get_dispatcher(Device.DEVICE_TYPE_ANDROID)
        self.assertEquals(dispatchers.dispatchers_cache, {1: dispatcher1})

        # Test cache iOS
        dispatcher2 = dispatchers.get_dispatcher(Device.DEVICE_TYPE_IOS)
        self.assertEquals(dispatchers.dispatchers_cache, {1: dispatcher1, 2: dispatcher2})

        # Final check, fetching from cache
        dispatcher1 = dispatchers.get_dispatcher(Device.DEVICE_TYPE_ANDROID)
        self.assertEquals(dispatchers.dispatchers_cache, {1: dispatcher1, 2: dispatcher2})

    def test_dispatcher_types(self):
        # Double check the factory method returning the correct types
        self.assertIsInstance(dispatchers.get_dispatcher(Device.DEVICE_TYPE_ANDROID), dispatchers.GCMDispatcher)
        self.assertIsInstance(dispatchers.get_dispatcher(Device.DEVICE_TYPE_IOS), dispatchers.APNSDispatcher)

    def test_dispatcher_android(self):
        android = dispatchers.get_dispatcher(Device.DEVICE_TYPE_ANDROID)

        device_key = 'TEST_DEVICE_KEY'
        data = {'title': 'Test', 'body': 'Test body'}

        # Check that we throw the proper exception in case no API Key is specified
        with mock.patch('django.conf.settings.PUSHY_GCM_API_KEY', new=None):
            self.assertRaises(PushGCMApiKeyException, android.send, device_key, data)

        with mock.patch('django.conf.settings.PUSHY_GCM_JSON_PAYLOAD', new=True):
            with mock.patch('gcm.GCM.json_request') as json_request_mock:
                android.send(device_key, data)

                self.assertTrue(json_request_mock.called)

        # Check result when canonical value is returned
        gcm = mock.Mock()
        gcm.return_value = 123123
        with mock.patch('gcm.GCM.plaintext_request', new=gcm):
            result, canonical_id = android.send(device_key, data)

            self.assertEquals(result, dispatchers.GCMDispatcher.PUSH_RESULT_SENT)
            self.assertEquals(canonical_id, 123123)

        # Check not registered exception
        gcm = mock.Mock(side_effect=GCMNotRegisteredException)
        with mock.patch('gcm.GCM.plaintext_request', new=gcm):
            result, canonical_id = android.send(device_key, data)

            self.assertEquals(result, dispatchers.GCMDispatcher.PUSH_RESULT_NOT_REGISTERED)
            self.assertEquals(canonical_id, 0)

        # Check IOError
        gcm = mock.Mock(side_effect=IOError)
        with mock.patch('gcm.GCM.plaintext_request', new=gcm):
            result, canonical_id = android.send(device_key, data)

            self.assertEquals(result, dispatchers.GCMDispatcher.PUSH_RESULT_EXCEPTION)
            self.assertEquals(canonical_id, 0)

        # Check all other exceptions
        gcm = mock.Mock(side_effect=PushException)
        with mock.patch('gcm.GCM.plaintext_request', new=gcm):
            result, canonical_id = android.send(device_key, data)

            self.assertEquals(result, dispatchers.GCMDispatcher.PUSH_RESULT_EXCEPTION)
            self.assertEquals(canonical_id, 0)

    @mock.patch('gcm.GCM.json_request')
    def test__send_json(self, json_request_mock):
        android = dispatchers.get_dispatcher(Device.DEVICE_TYPE_ANDROID)

        assert isinstance(android, dispatchers.GCMDispatcher)

        api_key = 'TEST_API_KEY'
        device_key = 'TEST_DEVICE_KEY'
        data = {'title': 'Test', 'body': 'Test body'}

        gcm_client = dispatchers.GCM(api_key)

        # Test canonical not update
        json_request_mock.return_value = {}
        self.assertEqual(android._send_json(gcm_client, device_key, data), 0)

        # Test canonical updated
        canonical_id = 'TEST_CANONICAL'
        json_request_mock.return_value = {
            'canonical': {
                device_key: canonical_id
            }
        }
        self.assertEqual(android._send_json(gcm_client, device_key, data), canonical_id)

        # Test Missing Registration
        json_request_mock.return_value = {
            'errors': {
                'NotRegistered': [device_key]
            }
        }
        self.assertRaises(dispatchers.GCMNotRegisteredException,
                          android._send_json, gcm_client, device_key, data)

        # Test handling unexpected (server) errors

        json_request_mock.return_value = {
            'errors': {
                'InternalServerError': [device_key]
            }
        }
        self.assertRaises(dispatchers.GCMUnavailableException,
                          android._send_json, gcm_client, device_key, data)


@mock.patch('pushy.dispatchers.APNSDispatcher._send_notification',
            new=lambda *a: dispatchers.APNSDispatcher.ErrorResponseEvent())
class ApnsDispatcherTests(TestCase):

    dispatcher = None

    device_key = 'TEST_DEVICE_KEY'

    data = {
        'alert': 'Test'
    }

    def setUp(self):
        self.dispatcher = dispatchers.get_dispatcher(Device.DEVICE_TYPE_IOS)

    @mock.patch('django.conf.settings.PUSHY_APNS_CERTIFICATE_FILE', new=None)
    def test_certificate_exception_on_send(self):
        self.assertRaises(PushAPNsCertificateException, self.dispatcher.send, self.device_key, self.data)

    @mock.patch('pushy.dispatchers.APNSDispatcher.ErrorResponseEvent.wait_for_response')
    def test_invalid_token_error_response(self, wait_for_response):
        wait_for_response.return_value = dispatchers.APNSDispatcher.STATUS_CODE_INVALID_TOKEN

        self.assertEqual(self.dispatcher.send(self.device_key, self.data),
                         (dispatchers.Dispatcher.PUSH_RESULT_NOT_REGISTERED, 0))

        wait_for_response.return_value = dispatchers.APNSDispatcher.STATUS_CODE_INVALID_TOKEN_SIZE

        self.assertEqual(self.dispatcher.send(self.device_key, self.data),
                         (dispatchers.Dispatcher.PUSH_RESULT_NOT_REGISTERED, 0))


    @mock.patch('pushy.dispatchers.APNSDispatcher.ErrorResponseEvent.wait_for_response')
    def test_push_exception(self, wait_for_response):
        wait_for_response.return_value = dispatchers.APNSDispatcher.STATUS_CODE_INVALID_PAYLOAD_SIZE

        self.assertEqual(self.dispatcher.send(self.device_key, self.data),
                         (dispatchers.Dispatcher.PUSH_RESULT_EXCEPTION, 0))

    @mock.patch('pushy.dispatchers.APNSDispatcher.ErrorResponseEvent.wait_for_response')
    def test_push_sent(self, wait_for_response):
        wait_for_response.return_value = dispatchers.APNSDispatcher.STATUS_CODE_NO_ERROR

        self.assertEqual(self.dispatcher.send(self.device_key, self.data),
                         (dispatchers.Dispatcher.PUSH_RESULT_SENT, 0))