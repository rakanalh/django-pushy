from gcm.gcm import GCMNotRegisteredException
import mock
from django.test import TestCase
from pushy.models import PushNotification, Device
from pushy.tasks import check_pending_push_notifications, send_push_notification_group


class TasksTestCase(TestCase):
    def test_pending_notifications(self):
        notification = PushNotification.objects.create(title='test',
                                                       body='test',
                                                       active=PushNotification.PUSH_ACTIVE,
                                                       sent=PushNotification.PUSH_NOT_SENT)

        mocked_task = mock.Mock()
        with mock.patch('pushy.tasks.create_push_notification_groups.apply_async', new=mocked_task):
            check_pending_push_notifications()

        notification = PushNotification.objects.get(pk=notification.id)
        self.assertEqual(notification.sent, PushNotification.PUSH_SENT)

    def test_send_notification_groups(self):
        notification = PushNotification.objects.create(title='test',
                                                       body='test',
                                                       active=PushNotification.PUSH_ACTIVE,
                                                       sent=PushNotification.PUSH_NOT_SENT)

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

