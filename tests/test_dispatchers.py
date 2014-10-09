import mock
from gcm.gcm import GCMNotRegisteredException

from django.test import TestCase

from pushy.exceptions import PushException, PushGCMApiKeyException

from pushy.models import Device
from pushy.dispatchers import get_dispatcher, dispatchers_cache, GCMDispatcher, APNSDispatcher


class DispatchersTestCase(TestCase):
    def test_check_cache(self):
        # Test cache Android
        dispatcher1 = get_dispatcher(Device.DEVICE_TYPE_ANDROID)
        self.assertEquals(dispatchers_cache, {1: dispatcher1})

        # Test cache iOS
        dispatcher2 = get_dispatcher(Device.DEVICE_TYPE_IOS)
        self.assertEquals(dispatchers_cache, {1: dispatcher1, 2: dispatcher2})

        # Final check, fetching from cache
        dispatcher1 = get_dispatcher(Device.DEVICE_TYPE_ANDROID)
        self.assertEquals(dispatchers_cache, {1: dispatcher1, 2: dispatcher2})

    def test_dispatcher_types(self):
        # Double check the factory method returning the correct types
        self.assertIsInstance(get_dispatcher(Device.DEVICE_TYPE_ANDROID), GCMDispatcher)
        self.assertIsInstance(get_dispatcher(Device.DEVICE_TYPE_IOS), APNSDispatcher)

    def test_dispatcher_android(self):
        android = get_dispatcher(Device.DEVICE_TYPE_ANDROID)

        device_key = 'TEST_DEVICE_KEY'
        data = {'title': 'Test', 'body': 'Test body'}

        # Check that we throw the proper exception in case no API Key is specified
        with mock.patch('django.conf.settings.PUSHY_GCM_API_KEY', new=None):
            self.assertRaises(PushGCMApiKeyException, android.send, device_key, data)

        # Check result when canonical value is returned
        gcm = mock.Mock()
        gcm.return_value = 123123
        with mock.patch('gcm.GCM.plaintext_request', new=gcm):
            result, canonical_id = android.send(device_key, data)

            self.assertEquals(result, GCMDispatcher.PUSH_RESULT_SENT)
            self.assertEquals(canonical_id, 123123)

        # Check not registered exception
        gcm = mock.Mock(side_effect=GCMNotRegisteredException)
        with mock.patch('gcm.GCM.plaintext_request', new=gcm):
            result, canonical_id = android.send(device_key, data)

            self.assertEquals(result, GCMDispatcher.PUSH_RESULT_NOT_REGISTERED)
            self.assertEquals(canonical_id, 0)

        # Check IOError
        gcm = mock.Mock(side_effect=IOError)
        with mock.patch('gcm.GCM.plaintext_request', new=gcm):
            result, canonical_id = android.send(device_key, data)

            self.assertEquals(result, GCMDispatcher.PUSH_RESULT_EXCEPTION)
            self.assertEquals(canonical_id, 0)

        # Check all other exceptions
        gcm = mock.Mock(side_effect=PushException)
        with mock.patch('gcm.GCM.plaintext_request', new=gcm):
            result, canonical_id = android.send(device_key, data)

            self.assertEquals(result, GCMDispatcher.PUSH_RESULT_EXCEPTION)
            self.assertEquals(canonical_id, 0)