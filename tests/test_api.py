from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class APITests(APITestCase):
    def setUp(self):
        self.email = 'test_user@some_domain.com'
        self.password = 'test_password'

        # self.user = User.objects.create_user(self.email, self.password)

    def test_create_device(self):
        data = {'key': 'KEY1', 'type': 'android'}

        response = self.create_device(data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, data)

    def test_create_device_ios(self):
        data = {'key': 'KEY1', 'type': 'ios'}

        response = self.create_device(data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, data)

    def test_create_device_unknown_type(self):
        data = {'key': 'KEY1', 'type': 'unknown'}

        response = self.create_device(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'type': ['"unknown" is not a valid choice.']})

    def test_create_duplicate_device(self):
        data = {'key': 'KEY1', 'type': 'android'}

        self.create_device(data)

        response = self.create_device(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['non_field_errors'][0],
                         'The fields key, type must make a unique set.')

    def test_destroy_device(self):
        data = {'key': 'KEY1', 'type': 'ios'}
        self.create_device(data)
        response = self.destroy_device(data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_destroy_nonexistent_device(self):
        response = self.destroy_device({'key': 'does not exist'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def create_device(self, data):
        url = reverse('pushy-devices')

        response = self.client.post(url, data, format='json')
        return response

    def destroy_device(self, data):
        url = reverse('pushy-devices')

        response = self.client.delete(url, data, format='json')
        return response
