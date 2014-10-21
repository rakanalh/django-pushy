import json
from django.contrib.auth import get_user_model
from gcm.gcm import GCMNotRegisteredException
import mock
from django.test import TestCase
from pushy.models import PushNotification, Device, get_filtered_devices_queryset
from pushy.tasks import check_pending_push_notifications, send_push_notification_group


class TasksTestCase(TestCase):
    def setUp(self):
        self.payload = {
            'key1': 'value1',
            'key2': 'value2',
        }

    def test_get_filtered_devices_queryset_on_type(self):
        notification = PushNotification.objects.create(
            title='test',
            payload=self.payload,
            active=PushNotification.PUSH_ACTIVE,
            sent=PushNotification.PUSH_NOT_SENT,
            filter_type=Device.DEVICE_TYPE_IOS
        )

        for _ in range(0, 3):
            Device.objects.create(
                key='TEST_DEVICE_KEY',
                type=Device.DEVICE_TYPE_IOS
            )

        for _ in range(0, 10):
            Device.objects.create(
                key='TEST_DEVICE_KEY',
                type=Device.DEVICE_TYPE_ANDROID
            )

        devices = get_filtered_devices_queryset(notification)
        self.assertEqual(devices.count(), 3)

    def test_get_filtered_devices_queryset_on_user(self):
        for i in range(0, 3):
            get_user_model().objects.create_user(
                username='test_user_%d' % i,
                email='test_user_%d@django-pushy.com' % i,
                password=i
            )

        user1 = get_user_model().objects.get(pk=1)
        user2 = get_user_model().objects.get(pk=2)

        # Add 5 devices to user2
        for _ in range(0, 5):
            Device.objects.create(
                key='TEST_DEVICE_KEY',
                type=Device.DEVICE_TYPE_ANDROID,
                user=user2
            )

        # Check that user2 has 5 devices
        notification = PushNotification.objects.create(
            title='test',
            payload=self.payload,
            active=PushNotification.PUSH_ACTIVE,
            sent=PushNotification.PUSH_NOT_SENT,
            filter_user=user2.id
        )

        devices = get_filtered_devices_queryset(notification)

        self.assertEqual(devices.count(), 5)

        # Check that user 1 has no devices
        notification = PushNotification.objects.create(
            title='test',
            payload=self.payload,
            active=PushNotification.PUSH_ACTIVE,
            sent=PushNotification.PUSH_NOT_SENT,
            filter_user=user1.id
        )

        devices = get_filtered_devices_queryset(notification)

        self.assertEqual(devices.count(), 0)

    def test_pending_notifications(self):
        notification = PushNotification.objects.create(
            title='test',
            payload=self.payload,
            active=PushNotification.PUSH_ACTIVE,
            sent=PushNotification.PUSH_NOT_SENT
        )

        mocked_task = mock.Mock()
        with mock.patch('pushy.tasks.create_push_notification_groups.apply_async', new=mocked_task):
            check_pending_push_notifications()

        notification = PushNotification.objects.get(pk=notification.id)
        self.assertEqual(notification.sent, PushNotification.PUSH_SENT)

    def test_send_notification_groups(self):
        notification = PushNotification.objects.create(
            title='test',
            payload=self.payload,
            active=PushNotification.PUSH_ACTIVE,
            sent=PushNotification.PUSH_NOT_SENT
        )

        # Assert return when the notification was not found
        self.assertFalse(send_push_notification_group(13, 0, 1))

        # Create a test device key
        device = Device.objects.create(key='TEST_DEVICE_KEY', type=Device.DEVICE_TYPE_ANDROID)

        # Make sure canonical ID is saved
        gcm = mock.Mock()
        gcm.return_value = 123123
        with mock.patch('gcm.GCM.plaintext_request', new=gcm):
            send_push_notification_group(notification.id, 0, 1)

            device = Device.objects.get(pk=device.id)
            self.assertEqual(device.key, '123123')

        # Make sure the key is deleted when not registered exception is fired
        gcm = mock.Mock()
        gcm.side_effect = GCMNotRegisteredException
        with mock.patch('gcm.GCM.plaintext_request', new=gcm):
            send_push_notification_group(notification.id, 0, 1)

            self.assertRaises(Device.DoesNotExist, Device.objects.get, pk=device.id)

