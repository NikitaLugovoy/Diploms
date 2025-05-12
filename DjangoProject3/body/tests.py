from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, Group
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.test import APIRequestFactory
from unittest.mock import patch, MagicMock
from body.models import Device, Office, Application, PackageDevice, OfficeLayout
from body.serializers import SendMessageSerializer
from body.views import update_device_condition_by_id, get_office_number, send_message_to_telegram
import json


class DeviceTests(TestCase):
    def setUp(self):
        # Создаем тестовые данные
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.office = Office.objects.create(number='101')
        self.package_device = PackageDevice.objects.create(number='P1', office=self.office)
        self.device = Device.objects.create(
            serial_number='SN123',
            condition_id=1,
            package=self.package_device
        )

    def test_update_device_condition_by_id(self):
        """Тестируем обновление состояния устройства."""
        device_id = self.device.id
        updated_device = update_device_condition_by_id(device_id)

        # Проверяем, что устройство обновлено
        self.assertEqual(updated_device.condition_id, 4)
        # Проверяем, что устройство в базе данных обновлено
        device_from_db = Device.objects.get(id=device_id)
        self.assertEqual(device_from_db.condition_id, 4)

    def test_update_device_condition_by_id_not_found(self):
        """Тестируем случай, когда устройство не найдено."""
        with self.assertRaises(Device.DoesNotExist):
            update_device_condition_by_id(999)  # Несуществующий ID

    def test_get_office_number(self):
        """Тестируем получение номера офиса."""
        office_id = self.office.id
        result = get_office_number(office_id)
        self.assertEqual(result, '101')

    def test_get_office_number_not_found(self):
        """Тестируем случай, когда офис не найден."""
        with self.assertRaises(Office.DoesNotExist):
            get_office_number(999)  # Несуществующий ID


class SendMessageToTelegramTests(TestCase):
    def setUp(self):
        # Настраиваем тестовые данные
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.group = Group.objects.create(name='master')
        self.user.groups.add(self.group)
        self.office = Office.objects.create(number='101')
        self.package_device = PackageDevice.objects.create(number='P1', office=self.office)
        self.device = Device.objects.create(
            serial_number='SN123',
            condition_id=1,
            package=self.package_device
        )
        self.factory = APIRequestFactory()

    @patch('requests.post')  # Мокаем HTTP-запрос для save_application
    @patch('telebot.TeleBot.send_message')  # Мокаем отправку сообщения в Telegram
    def test_send_message_to_telegram_success(self, mock_telegram, mock_requests_post):
        """Тестируем успешную отправку сообщения в Telegram и создание заявки."""
        # Настраиваем моки
        mock_requests_post.return_value = MagicMock(status_code=201)
        mock_telegram.return_value = None

        # Формируем данные запроса (без breakdown_type)
        data = {
            'message': 'Test message',
            'selected_filtered_devices': [self.device.id]
        }

        # Создаем запрос
        request = self.factory.post('/send-message/', data, format='json')
        request.user = self.user  # Привязываем пользователя

        # Вызываем view
        response = send_message_to_telegram(request)

        # Проверяем ответ
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')
        self.assertEqual(response_data['message'], 'Сообщение отправлено!')

        # Проверяем, что заявка создана
        self.assertTrue(Application.objects.filter(device_id=self.device.id).exists())
        # Проверяем, что состояние устройства обновлено
        updated_device = Device.objects.get(id=self.device.id)
        self.assertEqual(updated_device.condition_id, 4)

    @patch('requests.post')
    def test_send_message_to_telegram_invalid_data(self, mock_requests_post):
        """Тестируем отправку с невалидными данными."""
        # Формируем невалидные данные (нет selected_filtered_devices)
        data = {
            'message': 'Test message'
        }

        # Создаем запрос
        request = self.factory.post('/send-message/', data, format='json')
        request.user = self.user

        # Вызываем view
        response = send_message_to_telegram(request)

        # Проверяем ответ
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'error')
        self.assertEqual(response_data['message'], 'Не выбрано ни одного устройства!')