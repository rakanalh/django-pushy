from django.contrib.auth import get_user_model
import mock
from django.test import TestCase
from pushy.utils import send_push_notification
from pushy.models import PushNotification, Device


class AddTaskTestCase(TestCase):
    def setUp(self):
        self.payload = {
            'key1': 'value1',
            'key2': 'value2',
        }

    def test_add_task(self):
        mock_task = mock.Mock()

        with mock.patch('pushy.tasks.create_push_notification_groups.delay',
                        new=mock_task) as mocked_task:
            send_push_notification('some test push notification', self.payload)
            notification = PushNotification.objects.latest('id')
            mocked_task.assert_called_once_with(
                notification=notification.to_dict()
            )

            self.assertEquals(notification.payload, self.payload)

    def test_add_task_filter_device(self):
        device = Device.objects.create(key='TEST_DEVICE_KEY',
                                       type=Device.DEVICE_TYPE_IOS)

        mock_task = mock.Mock()
        with mock.patch('pushy.tasks.send_single_push_notification.apply_async',
                        new=mock_task) as mocked_task:
            send_push_notification(
                'some other test push notification',
                self.payload,
                device=device
            )

            notification = PushNotification.objects.latest('id')

            mocked_task.assert_called_with(kwargs={
                'device': device.id,
                'notification': notification.to_dict()
            })

    def test_add_task_filter_on_user(self):
        user = get_user_model().objects.create_user(
            username='test_user',
            email='test_user@django-pushy.com',
            password='test_password'
        )

        mock_task = mock.Mock()
        with mock.patch('pushy.tasks.create_push_notification_groups.delay',
                        new=mock_task) as mocked_task:
            send_push_notification(
                'some other test push notification',
                self.payload,
                filter_user=user.id
            )

            notification = PushNotification.objects.latest('id')

            mocked_task.assert_called_with(notification=notification.to_dict())
            self.assertEqual(notification.filter_user, user.id)
            self.assertEqual(notification.filter_type, 0)

    def test_add_task_filter_on_device_type(self):
        mock_task = mock.Mock()
        with mock.patch('pushy.tasks.create_push_notification_groups.delay',
                        new=mock_task) as mocked_task:
            send_push_notification(
                'some other test push notification',
                self.payload,
                filter_type=Device.DEVICE_TYPE_IOS
            )

            notification = PushNotification.objects.latest('id')

            mocked_task.assert_called_with(notification=notification.to_dict())
            self.assertEqual(notification.filter_user, 0)
            self.assertEqual(notification.filter_type, Device.DEVICE_TYPE_IOS)

    def test_add_task_filter_on_device_type_and_user(self):
        user = get_user_model().objects.create_user(
            username='test_user',
            email='test_user@django-pushy.com',
            password='test_password'
        )

        mock_task = mock.Mock()
        with mock.patch('pushy.tasks.create_push_notification_groups.delay',
                        new=mock_task) as mocked_task:
            send_push_notification(
                'some other test push notification', self.payload,
                filter_type=Device.DEVICE_TYPE_IOS,
                filter_user=user.id
            )

            notification = PushNotification.objects.latest('id')

            mocked_task.assert_called_with(notification=notification.to_dict())
            self.assertEqual(notification.filter_user, user.id)
            self.assertEqual(notification.filter_type, Device.DEVICE_TYPE_IOS)

    def test_add_task_without_storage(self):
        with mock.patch('pushy.tasks.create_push_notification_groups.delay'):
            notification = send_push_notification(
                'test', {},
                filter_type=Device.DEVICE_TYPE_IOS,
                store=False
            )

            self.assertIsNone(notification.id)
