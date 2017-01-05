from django.test import TestCase

from pushy.models import PushNotification


class TasksTestCase(TestCase):
    def test_empty_payload(self):
        notification = PushNotification()
        self.assertEqual(None, notification.payload)

    def test_valid_payload(self):
        payload = {
            'attr': 'value'
        }
        notification = PushNotification()
        notification.payload = payload

        self.assertEqual(payload, notification.payload)
