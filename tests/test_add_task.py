import mock
from django.test import TestCase
from pushy.utils import send_push_notification
from pushy.models import PushNotification


class AddTaskTestCase(TestCase):
    def test_add_task(self):
        title = 'Test'
        body = 'Testing notifications'

        mock_task = mock.Mock()

        with mock.patch('pushy.tasks.create_push_notification_groups.delay', new=mock_task) as mocked_task:
            send_push_notification(title, body)
            notification = PushNotification.objects.latest('id')
            mocked_task.assert_called_once_with(notification_id=notification.id)

            self.assertEquals(notification.title, title)
            self.assertEquals(notification.body, body)


