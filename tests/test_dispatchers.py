import mock

from django.test import TestCase

from pushjack.apns import APNSSandboxClient
from pushjack.exceptions import (
    GCMMissingRegistrationError,
    GCMInvalidPackageNameError,
    GCMTimeoutError,
    GCMAuthError,
    APNSAuthError,
    APNSMissingTokenError,
    APNSProcessingError,
    APNSShutdownError
)

from pushy.exceptions import (
    PushInvalidTokenException,
    PushInvalidDataException,
    PushAuthException,
    PushServerException
)

from pushy.models import Device
from pushy import dispatchers

from .data import (
    valid_response,
    valid_with_canonical_id_response,
    invalid_with_exception
)


class DispatchersTestCase(TestCase):

    def test_check_cache(self):
        dispatchers.dispatchers_cache = {}

        # Test cache Android
        dispatcher1 = dispatchers.get_dispatcher(Device.DEVICE_TYPE_ANDROID)
        self.assertEquals(dispatchers.dispatchers_cache, {1: dispatcher1})

        # Test cache iOS
        dispatcher2 = dispatchers.get_dispatcher(Device.DEVICE_TYPE_IOS)
        self.assertEquals(
            dispatchers.dispatchers_cache,
            {1: dispatcher1, 2: dispatcher2}
        )

        # Final check, fetching from cache
        dispatcher1 = dispatchers.get_dispatcher(Device.DEVICE_TYPE_ANDROID)
        dispatcher2 = dispatchers.get_dispatcher(Device.DEVICE_TYPE_IOS)
        self.assertEquals(
            dispatchers.dispatchers_cache,
            {1: dispatcher1, 2: dispatcher2}
        )

    def test_dispatcher_types(self):
        # Double check the factory method returning the correct types
        self.assertIsInstance(
            dispatchers.get_dispatcher(Device.DEVICE_TYPE_ANDROID),
            dispatchers.GCMDispatcher
        )
        self.assertIsInstance(
            dispatchers.get_dispatcher(Device.DEVICE_TYPE_IOS),
            dispatchers.APNSDispatcher
        )


class GCMDispatcherTestCase(TestCase):
    device_key = 'TEST_DEVICE_KEY'
    data = {'title': 'Test', 'body': 'Test body'}

    def test_constructor_with_api_key(self):
        dispatcher = dispatchers.GCMDispatcher(123)
        self.assertEquals(123, dispatcher._api_key)

    def test_send_with_no_api_key(self):
        # Check that we throw the proper exception
        # in case no API Key is specified
        with mock.patch('django.conf.settings.PUSHY_GCM_API_KEY', new=None):
            dispatcher = dispatchers.GCMDispatcher()
            self.assertRaises(
                PushAuthException,
                dispatcher.send,
                self.device_key,
                self.data
            )

    def test_notification_sent(self):
        dispatcher = dispatchers.GCMDispatcher()
        with mock.patch('pushjack.GCMClient.send') as request_mock:
            request_mock.return_value = valid_response()
            dispatcher.send(self.device_key, self.data)
            self.assertTrue(request_mock.called)

    def test_notification_sent_with_canonical_id(self):
        dispatcher = dispatchers.GCMDispatcher()
        # Check result when canonical value is returned
        response_mock = mock.Mock()
        response_mock.return_value = valid_with_canonical_id_response(123123)
        with mock.patch('pushjack.GCMClient.send', new=response_mock):
            canonical_id = dispatcher.send(self.device_key, self.data)
            self.assertEquals(canonical_id, 123123)

    def test_invalid_token_exception(self):
        dispatcher = dispatchers.GCMDispatcher()
        # Check not registered exception
        response_mock = mock.Mock()
        response_mock.return_value = invalid_with_exception(
            GCMAuthError('')
        )
        with mock.patch('pushjack.GCMClient.send', new=response_mock):
            self.assertRaises(
                PushAuthException,
                dispatcher.send,
                self.device_key,
                self.data
            )

    def test_invalid_api_key_exception(self):
        dispatcher = dispatchers.GCMDispatcher()
        # Check not registered exception
        response_mock = mock.Mock()
        response_mock.return_value = invalid_with_exception(
            GCMMissingRegistrationError('')
        )
        with mock.patch('pushjack.GCMClient.send', new=response_mock):
            self.assertRaises(
                PushInvalidTokenException,
                dispatcher.send,
                self.device_key,
                self.data
            )

    def test_invalid_data_exception(self):
        dispatcher = dispatchers.GCMDispatcher()
        # Check not registered exception
        response_mock = mock.Mock()
        response_mock.return_value = invalid_with_exception(
            GCMInvalidPackageNameError('')
        )
        with mock.patch('pushjack.GCMClient.send', new=response_mock):
            self.assertRaises(
                PushInvalidDataException,
                dispatcher.send,
                self.device_key,
                self.data
            )

    def test_invalid_exception(self):
        dispatcher = dispatchers.GCMDispatcher()
        # Check not registered exception
        response_mock = mock.Mock()
        response_mock.return_value = invalid_with_exception(
            GCMTimeoutError('')
        )
        with mock.patch('pushjack.GCMClient.send', new=response_mock):
            self.assertRaises(
                PushServerException,
                dispatcher.send,
                self.device_key,
                self.data
            )


class ApnsDispatcherTests(TestCase):
    device_key = 'TEST_DEVICE_KEY'
    data = {'alert': 'Test'}

    def setUp(self):
        self.dispatcher = dispatchers.get_dispatcher(Device.DEVICE_TYPE_IOS)

    @mock.patch('django.conf.settings.PUSHY_APNS_CERTIFICATE_FILE', new=None)
    def test_certificate_exception_on_send(self):
        self.assertRaises(
            PushAuthException,
            self.dispatcher.send,
            self.device_key,
            self.data
        )

    @mock.patch('django.conf.settings.PUSHY_APNS_SANDBOX', new=True)
    def test_sandbox_client(self):
        dispatcher = dispatchers.APNSDispatcher()
        dispatcher.establish_connection()
        self.assertIsInstance(dispatcher._client, APNSSandboxClient)

    def test_invalid_token_exception(self):
        # Check not registered exception
        response_mock = mock.Mock()
        response_mock.return_value = invalid_with_exception(
            APNSMissingTokenError('')
        )
        with mock.patch('pushjack.APNSClient.send', new=response_mock):
            self.assertRaises(
                PushInvalidTokenException,
                self.dispatcher.send,
                self.device_key,
                self.data
            )

    def test_invalid_api_key_exception(self):
        # Check not registered exception
        response_mock = mock.Mock()
        response_mock.return_value = invalid_with_exception(
            APNSAuthError('')
        )
        with mock.patch('pushjack.APNSClient.send', new=response_mock):
            self.assertRaises(
                PushAuthException,
                self.dispatcher.send,
                self.device_key,
                self.data
            )

    def test_invalid_data_exception(self):
        # Check not registered exception
        response_mock = mock.Mock()
        response_mock.return_value = invalid_with_exception(
            APNSProcessingError('')
        )
        with mock.patch('pushjack.APNSClient.send', new=response_mock):
            self.assertRaises(
                PushInvalidDataException,
                self.dispatcher.send,
                self.device_key,
                self.data
            )

    def test_invalid_exception(self):
        # Check not registered exception
        response_mock = mock.Mock()
        response_mock.return_value = invalid_with_exception(
            APNSShutdownError('')
        )
        with mock.patch('pushjack.APNSClient.send', new=response_mock):
            self.assertRaises(
                PushServerException,
                self.dispatcher.send,
                self.device_key,
                self.data
            )

    def test_push_sent(self):
        apns = mock.Mock()
        apns.return_value = valid_response()
        with mock.patch('pushjack.APNSClient.send', new=apns):
            self.assertEqual(
                self.dispatcher.send(self.device_key, self.data),
                None
            )
