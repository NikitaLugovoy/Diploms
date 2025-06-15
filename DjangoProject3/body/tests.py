from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.models import User, Group
from django.http import JsonResponse
from rest_framework.test import APIRequestFactory
from unittest.mock import patch, MagicMock
from body.models import (
    Body, Floor, Office, PackageDevice, Device, Application, Status, BreakdownType, OfficeLayout
)
from account.models import UserProfile
from type_devices.models import TypeDevice
from body.serializers import (
    SendMessageSerializer, SaveApplicationSerializer, ApplicationSerializer, CloseApplicationSerializer,
    OfficeSerializer, OfficeLayoutSerializer
)
from body.views import (
    application_list, close_application, save_application, update_device_condition_by_id,
    get_office_number, send_message_to_telegram, body_list, fastapplication_list,
    yagpt_page, user_dashboard, delete_application, device_breakdown_stats
)
import json
from django.urls import reverse
from django.utils import timezone
from datetime import datetime
import pytz


class BodyViewsTests(TestCase):
    def setUp(self):
        # Create test data
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.master_user = User.objects.create_user(username='master', password='masterpass')
        self.master_group = Group.objects.create(name='master')
        self.master_user.groups.add(self.master_group)

        self.body = Body.objects.create(number='B1', address='Test Address')
        self.floor = Floor.objects.create(number=1)
        self.office = Office.objects.create(number='101', floor=self.floor, body=self.body)
        self.package_device = PackageDevice.objects.create(number='P1', office=self.office)

        # Create Status objects with specific IDs
        self.status_broken = Status.objects.create(id=1, name='Broken')
        self.status_closed = Status.objects.create(id=3, name='Closed')
        self.status_faulty = Status.objects.create(id=4, name='Faulty')

        self.breakdown_type = BreakdownType.objects.create(name='Hardware Failure')
        self.type_device = TypeDevice.objects.create(name='Computer')

        self.device = Device.objects.create(
            serial_number='SN123',
            condition=self.status_broken,
            package=self.package_device,
            type=self.type_device
        )
        # Create application for regular user
        self.application = Application.objects.create(
            office=self.office,
            device=self.device,
            reason='Test reason',
            user=self.user,
            data=timezone.now(),
            status=self.status_broken,
            breakdown_type=self.breakdown_type
        )
        # Create application for master user
        self.master_application = Application.objects.create(
            office=self.office,
            device=self.device,
            reason='Master test reason',
            user=self.master_user,
            data=timezone.now(),
            status=self.status_broken,
            breakdown_type=self.breakdown_type
        )
        self.factory = APIRequestFactory()
        self.request_factory = RequestFactory()
        self.client = Client()

    def test_application_list_master(self):
        """Test application_list for master role."""
        request = self.factory.get('/applications/', {'status_id': '1'})
        request.user = self.master_user
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'

        response = application_list(request)
        self.assertEqual(response.status_code, 200)
        response_data = response.data
        self.assertEqual(len(response_data), 2)  # Expect two applications
        reasons = [app['reason'] for app in response_data]
        self.assertIn('Test reason', reasons)
        self.assertIn('Master test reason', reasons)

    def test_application_list_non_master(self):
        """Test application_list for non-master user."""
        request = self.factory.get('/applications/', {'status_id': '1'})
        request.user = self.user
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'

        response = application_list(request)
        self.assertEqual(response.status_code, 200)
        response_data = response.data
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['user'], self.user.id)

    def test_close_application(self):
        """Test closing an application."""
        request = self.factory.post(f'/close/{self.application.id}/')
        request.user = self.user

        response = close_application(request, self.application.id)
        self.assertEqual(response.status_code, 302)  # Redirect
        application = Application.objects.get(id=self.application.id)
        device = Device.objects.get(id=self.device.id)
        self.assertEqual(application.status_id, 3)
        self.assertEqual(device.condition_id, 1)

    def test_save_application(self):
        """Test saving a new application."""
        data = {
            'office_id': self.office.id,
            'device_ids': [self.device.id],
            'reason': 'New issue',
            'breakdown_type_id': self.breakdown_type.id,
            'user_id': self.user.id
        }
        request = self.factory.post('/save-application/', data, format='json')

        response = save_application(request)
        self.assertEqual(response.status_code, 201)
        response_data = response.data
        self.assertEqual(response_data['status'], 'success')
        self.assertTrue(Application.objects.filter(reason='New issue').exists())

    def test_update_device_condition_by_id(self):
        """Test updating device condition."""
        device = update_device_condition_by_id(self.device.id)
        self.assertEqual(device.condition_id, 4)
        device_from_db = Device.objects.get(id=self.device.id)
        self.assertEqual(device_from_db.condition_id, 4)

    def test_get_office_number(self):
        """Test getting office number."""
        result = get_office_number(self.office.id)
        self.assertEqual(result, '101')

    @patch('requests.post')
    @patch('telebot.TeleBot.send_message')
    def test_send_message_to_telegram_success(self, mock_telegram, mock_requests_post):
        """Test successful Telegram message sending."""
        mock_requests_post.return_value = MagicMock(status_code=201)
        mock_telegram.return_value = None

        data = {
            'message': 'Test message',
            'selected_filtered_devices': [self.device.id],  # Use correct device ID
            'breakdown_type': self.breakdown_type.id  # Use correct breakdown type ID
        }
        request = self.factory.post('/send-message/', data, format='json')
        request.user = self.user

        response = send_message_to_telegram(request)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')
        self.assertTrue(Application.objects.filter(device_id=self.device.id).exists())
        updated_device = Device.objects.get(id=self.device.id)
        self.assertEqual(updated_device.condition_id, 4)

    def test_body_list_get(self):
        """Test GET request for body_list."""
        request = self.request_factory.get('/bodies/')
        request.user = self.user

        response = body_list(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'bodies')
        self.assertContains(response, 'floors')
        self.assertContains(response, 'offices')

    @patch('requests.get')
    def test_fastapplication_list_get(self, mock_requests_get):
        """Test GET request for fastapplication_list."""
        mock_requests_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [{'startAt': '09:00:00', 'endAt': '17:00:00', 'classroom': '101'}]
        )
        request = self.request_factory.get('/fastapplications/')
        request.user = self.user

        response = fastapplication_list(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'schedules')
        self.assertContains(response, 'offices')

    @patch('requests.post')
    def test_yagpt_page_post_text(self, mock_requests_post):
        """Test POST request for yagpt_page with text."""
        mock_requests_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {'result': {'alternatives': [{'message': {'text': 'Test response'}}]}}
        )
        data = {'user_text': 'Test query'}
        self.client.force_login(self.user)  # Authenticate user
        response = self.client.post('/body/yagpt/', data)  # Temporary direct URL

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['generated_text'], 'Test response'[:20])

    def test_user_dashboard_master(self):
        """Test user_dashboard for master role."""
        request = self.request_factory.get('/dashboard/')
        request.user = self.master_user

        response = user_dashboard(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '101')  # Check for office number
        self.assertContains(response, 'Master test reason')  # Check for master application

    def test_delete_application(self):
        """Test deleting an application."""
        request = self.factory.post(f'/delete/{self.application.id}/')
        request.user = self.user

        response = delete_application(request, self.application.id)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Application.objects.filter(id=self.application.id).exists())

    def test_device_breakdown_stats(self):
        """Test device_breakdown_stats."""
        request = self.factory.get('/stats/', {'office_id': self.office.id})
        request.user = self.user
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'

        response = device_breakdown_stats(request)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIn('broken_devices', response_data)
        self.assertIn('breakdown_type_data', response_data)