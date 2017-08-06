import datetime
import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone

from pushy.models import (
    PushNotification,
    Device,
    get_filtered_devices_queryset
)

from pushy.exceptions import (
    PushException,
    PushInvalidTokenException
)

from pushy.tasks import (
    check_pending_push_notifications,
    send_push_notification_group,
    send_single_push_notification,
    create_push_notification_groups,
    clean_sent_notifications,
    notify_push_notification_sent
)


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

        for i in range(0, 3):
            Device.objects.create(
                key='TEST_DEVICE_KEY_{}'.format(i),
                type=Device.DEVICE_TYPE_IOS
            )

        for i in range(0, 10):
            Device.objects.create(
                key='TEST_DEVICE_KEY_{}'.format(i),
                type=Device.DEVICE_TYPE_ANDROID
            )

        devices = get_filtered_devices_queryset(notification.to_dict())
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
        for i in range(0, 5):
            Device.objects.create(
                key='TEST_DEVICE_KEY_{}'.format(i),
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

        devices = get_filtered_devices_queryset(notification.to_dict())

        self.assertEqual(devices.count(), 5)

        # Check that user 1 has no devices
        notification = PushNotification.objects.create(
            title='test',
            payload=self.payload,
            active=PushNotification.PUSH_ACTIVE,
            sent=PushNotification.PUSH_NOT_SENT,
            filter_user=user1.id
        )

        devices = get_filtered_devices_queryset(notification.to_dict())

        self.assertEqual(devices.count(), 0)

    def test_pending_notifications(self):
        PushNotification.objects.create(
            title='test',
            payload=self.payload,
            active=PushNotification.PUSH_ACTIVE,
            sent=PushNotification.PUSH_NOT_SENT
        )

        mocked_task = mock.Mock()
        with mock.patch(
                'pushy.tasks.create_push_notification_groups.apply_async',
                new=mocked_task):
            check_pending_push_notifications()
            mocked_task.assert_called()

    def test_notifications_groups_chord(self):
        notification = PushNotification.objects.create(
            title='test',
            payload=self.payload,
            active=PushNotification.PUSH_ACTIVE,
            sent=PushNotification.PUSH_NOT_SENT
        )

        # Create a test device key
        Device.objects.create(
            key='TEST_DEVICE_KEY_ANDROID',
            type=Device.DEVICE_TYPE_ANDROID
        )

        mocked_task = mock.Mock()
        with mock.patch(
                'celery.chord',
                new=mocked_task):
            create_push_notification_groups(notification.to_dict())
            mocked_task.assert_called()

    def test_notifications_groups_return(self):
        notification = PushNotification.objects.create(
            title='test',
            payload=self.payload,
            active=PushNotification.PUSH_ACTIVE,
            sent=PushNotification.PUSH_NOT_SENT
        )

        # Create a test device key
        Device.objects.create(
            key='TEST_DEVICE_KEY_ANDROID',
            type=Device.DEVICE_TYPE_ANDROID
        )

        mocked_task = mock.Mock()
        with mock.patch(
                'celery.chord',
                new=mocked_task):
            notification_dict = notification.to_dict()
            notification_dict['id'] = None
            create_push_notification_groups(notification_dict)

            notification = PushNotification.objects.get(pk=notification.id)
            self.assertEqual(PushNotification.PUSH_NOT_SENT, notification.sent)

    def test_send_notification_groups(self):
        notification = PushNotification.objects.create(
            title='test',
            payload=self.payload,
            active=PushNotification.PUSH_ACTIVE,
            sent=PushNotification.PUSH_NOT_SENT
        )

        # Create a test device key
        device = Device.objects.create(
            key='TEST_DEVICE_KEY_ANDROID',
            type=Device.DEVICE_TYPE_ANDROID
        )

        # Make sure canonical ID is saved
        gcm = mock.Mock()
        gcm.return_value = 123123
        with mock.patch('pushy.dispatchers.GCMDispatcher.send', new=gcm):
            send_push_notification_group(notification.to_dict(), 0, 1)

            device = Device.objects.get(pk=device.id)
            self.assertEqual(device.key, '123123')

        # Make sure the key is deleted when not registered exception is fired
        gcm = mock.Mock()
        gcm.side_effect = PushInvalidTokenException
        with mock.patch('pushy.dispatchers.GCMDispatcher.send', new=gcm):
            send_push_notification_group(notification.to_dict(), 0, 1)

            self.assertRaises(
                Device.DoesNotExist,
                Device.objects.get,
                pk=device.id
            )

        # Create an another test device key
        device = Device.objects.create(
            key='TEST_DEVICE_KEY_ANDROID2',
            type=Device.DEVICE_TYPE_ANDROID
        )

        # No canonical ID wasn't returned
        gcm = mock.Mock()
        gcm.return_value = False
        with mock.patch('pushy.dispatchers.GCMDispatcher.send', new=gcm):
            send_push_notification_group(notification.to_dict(), 0, 1)

            device = Device.objects.get(pk=device.id)
            self.assertEqual(device.key, 'TEST_DEVICE_KEY_ANDROID2')

    def test_delete_old_key_if_canonical_is_registered(self):
        notification = PushNotification.objects.create(
            title='test',
            payload=self.payload,
            active=PushNotification.PUSH_ACTIVE,
            sent=PushNotification.PUSH_NOT_SENT
        )
        # Create a test device key
        device = Device.objects.create(
            key='TEST_DEVICE_KEY_ANDROID',
            type=Device.DEVICE_TYPE_ANDROID
        )
        Device.objects.create(key='123123', type=Device.DEVICE_TYPE_ANDROID)

        # Make sure old device is deleted
        # if the new canonical ID already exists
        gcm = mock.Mock()
        gcm.return_value = '123123'
        with mock.patch('pushy.dispatchers.GCMDispatcher.send', new=gcm):
            send_push_notification_group(notification.to_dict(), 0, 1)

            self.assertFalse(Device.objects.filter(pk=device.id).exists())

    def test_create_push_notification_groups_non_existent_notification(self):
        result = create_push_notification_groups({'id': 1000})
        self.assertFalse(result)

    def test_non_existent_device(self):
        result = send_single_push_notification(1000, {'payload': 'test'})
        self.assertFalse(result)

    def test_invalid_token_exception(self):
        # Create a test device key
        device = Device.objects.create(
            key='TEST_DEVICE_KEY_ANDROID',
            type=Device.DEVICE_TYPE_ANDROID
        )
        gcm = mock.Mock()
        gcm.side_effect = PushInvalidTokenException
        with mock.patch('pushy.dispatchers.GCMDispatcher.send', new=gcm):
            send_single_push_notification(device, {'payload': 'test'})
            self.assertRaises(
                Device.DoesNotExist,
                Device.objects.get,
                pk=device.id
            )

    @mock.patch('pushy.tasks.logger.exception')
    def test_push_exception(self, logging_mock):
        # Create a test device key
        device = Device.objects.create(
            key='TEST_DEVICE_KEY_ANDROID',
            type=Device.DEVICE_TYPE_ANDROID
        )
        gcm = mock.Mock()
        gcm.side_effect = PushException
        with mock.patch('pushy.dispatchers.GCMDispatcher.send', new=gcm):
            send_single_push_notification(device, {'payload': 'test'})

            logging_mock.assert_called()

    def test_delete_old_notifications_undefine_max_age(self):
        self.assertRaises(ValueError, clean_sent_notifications)

    @override_settings(PUSHY_NOTIFICATION_MAX_AGE=datetime.timedelta(days=90))
    def test_delete_old_notifications(self):
        for i in range(10):
            date_started = timezone.now() - datetime.timedelta(days=91)
            date_finished = date_started
            notification = PushNotification()
            notification.title = 'title {}'.format(i)
            notification.body = '{}'
            notification.sent = PushNotification.PUSH_SENT
            notification.date_started = date_started
            notification.date_finished = date_finished
            notification.save()

        clean_sent_notifications()

        self.assertEquals(PushNotification.objects.count(), 0)

    @override_settings(PUSHY_NOTIFICATION_MAX_AGE=datetime.timedelta(days=90))
    def test_delete_old_notifications_with_remaining_onces(self):
        for i in range(10):
            date_started = timezone.now() - datetime.timedelta(days=91)
            date_finished = date_started
            notification = PushNotification()
            notification.title = 'title {}'.format(i)
            notification.body = '{}'
            notification.sent = PushNotification.PUSH_SENT
            notification.date_started = date_started
            notification.date_finished = date_finished
            notification.save()

        for i in range(10):
            date_started = timezone.now() - datetime.timedelta(days=61)
            date_finished = date_started
            notification = PushNotification()
            notification.title = 'title {}'.format(i)
            notification.body = '{}'
            notification.sent = PushNotification.PUSH_SENT
            notification.date_started = date_started
            notification.date_finished = date_finished
            notification.save()

        clean_sent_notifications()

        self.assertEquals(PushNotification.objects.count(), 10)

    def test_notify_notification_finished(self):
        notification = PushNotification.objects.create(
            title='test',
            payload=self.payload,
            active=PushNotification.PUSH_ACTIVE,
            sent=PushNotification.PUSH_NOT_SENT
        )
        notification.save()
        notify_push_notification_sent(notification.to_dict())

        notification = PushNotification.objects.get(pk=notification.id)
        self.assertEquals(PushNotification.PUSH_SENT, notification.sent)

    def test_notify_notification_does_not_exist(self):
        notification = PushNotification(
            id=1001,
            title='test',
            payload=self.payload,
            active=PushNotification.PUSH_ACTIVE,
            sent=PushNotification.PUSH_NOT_SENT
        )

        notify_push_notification_sent(notification.to_dict())
        self.assertEquals(PushNotification.PUSH_NOT_SENT, notification.sent)

    def test_notify_notification_does_nothing(self):
        notification = PushNotification(
            title='test',
            payload=self.payload,
            active=PushNotification.PUSH_ACTIVE,
            sent=PushNotification.PUSH_NOT_SENT
        )

        self.assertFalse(notify_push_notification_sent(notification.to_dict()))
