import json
from unittest.mock import patch, Mock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient
from django.conf import settings

class SendMessageToTelegramTests(TestCase):
    fixtures = ['body_test_data.json']

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.get(pk=1)  # Получение пользователя из фикстуры (pk=1)
        self.client.force_authenticate(user=self.user)  # Аутентификация пользователя

        self.valid_payload = {
            'message': 'Test message',
            'selected_filtered_devices': [1],  # Device pk=1
            'breakdown_type': 1  # BreakdownType pk=1
        }

    @patch('body.views.requests.post')
    @patch('body.views.get_telegram_bot')
    def test_send_message_to_telegram_success(self, mock_get_telegram_bot, mock_requests_post):
        mock_bot = Mock()
        mock_get_telegram_bot.return_value = mock_bot

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.raise_for_status = Mock()
        mock_requests_post.return_value = mock_response

        response = self.client.post(
            reverse('send_message_to_telegram'),
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'status': 'success', 'message': 'Сообщение отправлено!'})
        self.assertEqual(mock_bot.send_message.called, True)
        self.assertEqual(mock_requests_post.called, True)
        self.assertEqual(
            mock_requests_post.call_args[0][0],
            f"{settings.BASE_URL}/body/save-application/"
        )
        self.assertEqual(
            mock_requests_post.call_args[1]['json'],
            {
                'office_id': 1,
                'device_ids': [1],
                'reason': 'Test message',
                'breakdown_type_id': 1,
                'user_id': 1
            }
        )

        from body.models import Device
        device = Device.objects.get(pk=1)
        self.assertEqual(device.condition_id, 4)

    @patch('body.views.requests.post')
    def test_send_message_to_telegram_no_devices(self, mock_requests_post):
        payload = {
            'message': 'Test message',
            'selected_filtered_devices': [],
            'breakdown_type': 1
        }

        response = self.client.post(
            reverse('send_message_to_telegram'),
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'status': 'error', 'message': 'Не выбрано ни одного устройства!'})
        self.assertEqual(mock_requests_post.called, False)

class BodyListTests(TestCase):
    fixtures = ['body_test_data.json']

    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()
        self.user = User.objects.get(pk=1)  # Получение пользователя из фикстуры (pk=1)
        self.client.force_login(self.user)  # Аутентификация для Client
        self.api_client.force_authenticate(user=self.user)  # Аутентификация для APIClient

    def test_body_list_get(self):
        response = self.client.get(reverse('body_list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'body/body_list.html')
        self.assertIn('bodies', response.context)
        self.assertIn('floors', response.context)
        self.assertIn('offices', response.context)
        self.assertEqual(response.context['role'], 'user')
        self.assertEqual(response.context['notifications_count'], 0)
        self.assertEqual(len(response.context['bodies']), 1)
        self.assertEqual(len(response.context['floors']), 1)
        self.assertEqual(len(response.context['offices']), 1)

    def test_body_list_post_with_filters(self):
        payload = {
            'selected_bodies': [1],  # Body pk=1
            'selected_floors': [1],  # Floor pk=1
            'selected_offices': [1],  # Office pk=1
            'selected_package_devices': [1],  # PackageDevice pk=1
            'selected_filtered_devices': [1]  # Device pk=1
        }

        response = self.api_client.post(
            reverse('body_list'),
            data=payload,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertIn('offices', response_data)
        self.assertIn('package_devices', response_data)
        self.assertIn('devices', response_data)
        self.assertIn('layouts', response_data)
        self.assertIn('breakdown_types', response_data)
        self.assertEqual(len(response_data['offices']), 1)
        self.assertEqual(len(response_data['package_devices']), 1)
        self.assertEqual(len(response_data['devices']), 1)
        self.assertEqual(len(response_data['layouts']), 1)
        self.assertEqual(response_data['package_devices'][0]['condition_id'], '1')
        self.assertEqual(response_data['breakdown_types'][0]['name'], 'Hardware Failure')

    def test_body_list_post_no_filters(self):
        payload = {
            'selected_bodies': [],
            'selected_floors': [],
            'selected_offices': [],
            'selected_package_devices': []
        }

        response = self.api_client.post(
            reverse('body_list'),
            data=payload,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertIn('offices', response_data)
        self.assertIn('package_devices', response_data)
        self.assertIn('devices', response_data)
        self.assertIn('layouts', response_data)
        self.assertEqual(len(response_data['offices']), 1)
        self.assertEqual(len(response_data['package_devices']), 0)
        self.assertEqual(len(response_data['devices']), 1)
        self.assertEqual(len(response_data['layouts']), 0)

    def test_body_list_post_master_role(self):
        from django.contrib.auth.models import Group
        group = Group.objects.get(pk=1)
        group.name = 'master'
        group.save()

        payload = {
            'selected_bodies': [1],
            'selected_floors': [1],
            'selected_offices': [1],
            'selected_package_devices': [1]
        }

        response = self.api_client.post(
            reverse('body_list'),
            data=payload,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(len(response_data['offices']), 1)
        self.assertEqual(len(response_data['package_devices']), 1)
        self.assertEqual(len(response_data['devices']), 1)
        self.assertEqual(response_data['package_devices'][0]['condition_id'], '1')