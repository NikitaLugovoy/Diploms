import logging

from collections import defaultdict

import pytz

import telebot
from django.contrib.auth import logout
from django.contrib.auth.views import PasswordChangeView
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from requests.exceptions import RequestException
from datetime import datetime
from django.conf import settings

from account.models import UserProfile
from .models import OfficeLayout, TelegramUser
from .serializers import OfficeLayoutSerializer, BodySerializer, FloorSerializer

from django.contrib.auth.decorators import login_required

from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import (
    PackageDevice, Device, Office, Body, Floor, Application, Status, BreakdownType
)

from .serializers import (
    DeviceSerializer, OfficeSerializer, SendMessageSerializer,
    ApplicationSerializer, CloseApplicationSerializer, SaveApplicationSerializer
)

from django.utils.timezone import now

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = settings.BOT_TOKEN
CHAT_ID = settings.CHAT_ID

import json
import pytesseract
from PIL import Image
import requests

from django.views.decorators.csrf import csrf_exempt
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view

from DjangoProject3 import settings

# https://oauth.yandex.ru/verification_code
OAUTH_TOKEN = settings.OAUTH_TOKEN
FOLDER_ID = settings.FOLDER_ID

# Устанавливаем путь к Tesseract
pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH


@swagger_auto_schema(method='get', responses={200: ApplicationSerializer(many=True)})
@api_view(["GET"])
def application_list(request):
    # Определяем роль пользователя
    user = request.user
    groups = user.groups.all()
    role = groups[0].name.lower() if groups.exists() else 'без роли'

    # Получаем status_id из GET-параметров
    status_id = request.GET.get("status_id")

    # Определяем, какие заявки отображать и считаем уведомления
    if role == "master":
        # Для мастера: все заявки с учетом статуса
        applications = Application.objects.select_related("office", "device", "status", "breakdown_type")
        if status_id:
            applications = applications.filter(status_id=status_id)
        else:
            applications = applications.filter(status_id=1)  # По умолчанию только "сломанные"
        notifications_count = Application.objects.filter(status_id=1).count()  # Все сломанные заявки
    else:
        # Для остальных ролей: только заявки текущего пользователя
        applications = Application.objects.select_related("office", "device", "status", "breakdown_type").filter(
            user=user)
        if status_id:
            applications = applications.filter(status_id=status_id)
        else:
            applications = applications.filter(status_id=1)  # По умолчанию только "сломанные"
        notifications_count = Application.objects.filter(user=user,
                                                         status_id=1).count()  # Заявки пользователя с status_id=1

    # Сортировка по дате
    applications = applications.order_by("-data")

    # Сериализация данных
    serializer = ApplicationSerializer(applications, many=True)

    # Отладочная информация
    print("🔹 Полученные данные:", serializer.data)

    # Если запрос AJAX, возвращаем JSON
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return Response(serializer.data)

    # Рендеринг шаблона
    statuses = Status.objects.all()  # Получаем все статусы для селекта
    return render(request, "body/application_list.html", {
        "applications": serializer.data,
        "statuses": statuses,
        "role": role,
        "notifications_count": notifications_count,
        'active_page': 'application_list'
    })


@swagger_auto_schema(method='post', request_body=CloseApplicationSerializer)
@api_view(['POST'])
def close_application(request, application_id):
    print(f"Received request to close application {application_id}")
    application = get_object_or_404(Application, id=application_id)
    print(f"Found application: {application}")

    application.status_id = 3
    application.save()

    device = get_object_or_404(Device, id=application.device_id)
    device.condition_id = 1
    device.save()

    logger.info(f"Application {application_id} closed successfully.")

    # Перенаправляем обратно на страницу списка заявок
    return redirect('application_list')


@swagger_auto_schema(method='post', request_body=SaveApplicationSerializer)
@api_view(['POST'])
def save_application(request):
    serializer = SaveApplicationSerializer(data=request.data)
    if serializer.is_valid():
        office_id = serializer.validated_data['office_id']
        device_ids = serializer.validated_data['device_ids']
        reason = serializer.validated_data['reason']
        breakdown_type_id = serializer.validated_data.get('breakdown_type_id')
        user_id = serializer.validated_data.get('user_id')

        application_ids = []
        for device_id in device_ids:
            application = Application.objects.create(
                office_id=office_id,
                device_id=device_id,
                reason=reason,
                user_id=user_id,
                data=now(),
                status_id=1,
                breakdown_type_id=breakdown_type_id
            )
            application.save()
            application_ids.append(application.id)

        logger.info("Applications saved successfully.")
        return Response(
            {'status': 'success', 'message': 'Applications saved successfully!', 'application_ids': application_ids},
            status=status.HTTP_201_CREATED)

    logger.error("Invalid application data received.")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def get_device(device_id):
    try:
        return Device.objects.get(id=device_id)
    except Device.DoesNotExist:
        return None


def update_device_condition_by_id(device_id: int):
    """
    Обновляет состояние устройства по ID (condition_id = 4).
    """
    device = get_object_or_404(Device, id=device_id)
    device.condition_id = 4
    device.save()
    return device  # Возвращаем объект устройства, а не Response


def get_body_address(body_id: int) -> str:
    """
    Получает адрес здания по ID и возвращает строку.
    """
    body = get_object_or_404(Body, id=body_id)
    return body.address  # Предполагаем, что у модели Body есть поле address


def get_office_number(office_id: int) -> Response:
    """
    Получает номер офиса по ID.
    """
    office = get_object_or_404(Office, id=office_id)
    return str(office.number)


# Кэшируем объект бота
def get_telegram_bot(token):
    if hasattr(get_telegram_bot, 'bot'):
        return get_telegram_bot.bot

    get_telegram_bot.bot = telebot.TeleBot(token)
    return get_telegram_bot.bot


# Отправка сообщения в Telegram
def send_telegram_message(chat_bot: str, chat_id: str, message: str):
    try:
        bot = get_telegram_bot(chat_bot)
        logger.info(f"Отправка сообщения в Telegram: {message}")  # Лог перед отправкой
        bot.send_message(chat_id, message)
    except Exception as e:
        logger.error(f"{send_telegram_message.__name__} {e}")


@swagger_auto_schema(
    method='post',
    request_body=SendMessageSerializer,
    responses={200: openapi.Response('Успешный ответ', SendMessageSerializer)},
    operation_description="Отправляет сообщение в Telegram и создает заявку.",
)
@api_view(['POST'])
@permission_classes([AllowAny])
def send_message_to_telegram(request):
    logger.info(f"RAW REQUEST DATA: {request.data}")

    serializer = SendMessageSerializer(data=request.data)
    if not serializer.is_valid():
        logger.error(f"Ошибка валидации: {serializer.errors}")
        return JsonResponse({'status': 'error', 'message': serializer.errors}, status=400)

    data = serializer.validated_data
    user_message = data.get('message', '')
    selected_filtered_devices = data.get('selected_filtered_devices', [])
    breakdown_type_id = request.data.get('breakdown_type')
    breakdown_type = BreakdownType.objects.get(id=breakdown_type_id)

    # Получение имени типа поломки
    breakdown_type_name = "Не указан"
    if breakdown_type_id:
        try:
            breakdown_type = BreakdownType.objects.get(id=breakdown_type_id)
            breakdown_type_name = breakdown_type.name
        except BreakdownType.DoesNotExist:
            logger.warning(f"Неизвестный тип поломки: {breakdown_type_id}")

    logger.info(f"Выбранный тип поломки: {breakdown_type_id}")
    if not selected_filtered_devices:
        return JsonResponse({'status': 'error', 'message': 'Не выбрано ни одного устройства!'}, status=400)

    # Получение информации об устройствах
    device_details_list = []
    first_office_id = None

    logger.info(f"------------- User ID: {request.user.id}")

    for device_id in selected_filtered_devices:
        try:
            # Используем select_related для оптимизации запросов
            device = Device.objects.select_related(
                'type',
                'package__office__floor',
                'package__office__body'
            ).get(id=device_id)

            updated_device = update_device_condition_by_id(device_id)
            package = device.package
            office = package.office
            floor = office.floor
            body = office.body

            if not first_office_id:
                first_office_id = office.id  # Запоминаем первый найденный офис

            device_details_list.append(
                f"Устройство ID: {device.id}\n"
                f"Тип устройства: {device.type.name}\n"
                f"Серийный номер: {device.serial_number}\n"
                f"Тип поломки: {breakdown_type.name}\n"
                f"ПК: {package.number}\n"
                f"Кабинет: {office.number}\n"
                f"Этаж: {floor.number}\n"
                f"Корпус: {body.number}, Адрес: {body.address}\n"
            )
        except Device.DoesNotExist:
            device_details_list.append(f"Неизвестное устройство (ID: {device_id})")

    # Формирование сообщения
    devices_info = "\n".join(device_details_list)
    formatted_message = f"Сообщение от пользователя: {user_message}\n\nИнформация об устройствах:\n{devices_info}"

    # Сохранение заявки через HTTP-запрос
    save_application_url = f"{settings.BASE_URL}/body/save-application/"
    try:
        response = requests.post(
            save_application_url,
            json={'office_id': first_office_id, 'device_ids': selected_filtered_devices, 'reason': user_message,
                  'breakdown_type_id': breakdown_type.id, 'user_id': request.user.id},
        )
        response.raise_for_status()
    except RequestException as e:
        logger.error(f"Ошибка при создании заявки: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Ошибка при создании заявки!'}, status=500)

    # Отправка сообщения в Telegram
    try:
        send_telegram_message(BOT_TOKEN, CHAT_ID, formatted_message)
        notify_all_users(BOT_TOKEN, f"Создана новая заявка!\n\n{formatted_message}")
        return JsonResponse({'status': 'success', 'message': 'Сообщение отправлено!'}, status=200)
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в Telegram: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def notify_all_users(bot_token: str, message: str):
    bot = get_telegram_bot(bot_token)
    for user in TelegramUser.objects.all():
        try:
            bot.send_message(user.chat_id, message)
        except Exception as e:
            logger.error(f"Ошибка отправки пользователю {user.chat_id}: {e}")

@swagger_auto_schema(
    method='get',
    operation_summary="Получение списка корпусов, этажей и офисов",
    responses={200: "Список корпусов, этажей и офисов"}
)
@swagger_auto_schema(
    method='post',
    operation_summary="Фильтрация офисов, пакетов устройств и устройств",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "selected_bodies": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER)),
            "selected_floors": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER)),
            "selected_offices": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER)),
            "selected_package_devices": openapi.Schema(type=openapi.TYPE_ARRAY,
                                                       items=openapi.Items(type=openapi.TYPE_INTEGER)),
        },
    ),
    responses={200: "Отфильтрованные офисы, пакеты устройств и устройства"}
)
@api_view(["GET", "POST"])
def body_list(request):
    user = request.user
    groups = user.groups.all()
    role = groups[0].name.lower() if groups.exists() else 'без роли'

    # Подсчет уведомлений
    if role == "master":
        notifications_count = Application.objects.filter(status_id=1).count()
    else:
        notifications_count = Application.objects.filter(user=user, status_id=1).count()

    if request.method == "POST":
        selected_bodies = list(map(int, request.POST.getlist("selected_bodies", [])))
        selected_floors = list(map(int, request.POST.getlist("selected_floors", [])))
        selected_offices = list(map(int, request.POST.getlist("selected_offices", [])))
        selected_package_devices = list(map(int, request.POST.getlist("selected_package_devices", [])))
        selected_filtered_devices = list(map(int, request.POST.getlist("selected_filtered_devices", [])))

        # Фильтрация этажей по выбранным корпусам
        floors = Floor.objects.all()
        if selected_bodies:
            floors = floors.filter(bodies__id__in=selected_bodies).distinct()

        # Фильтрация офисов
        offices = Office.objects.all()
        if selected_bodies:
            offices = offices.filter(body_id__in=selected_bodies)
        if selected_floors:
            offices = offices.filter(floor_id__in=selected_floors)

        # Фильтрация пакетов устройств
        package_devices = PackageDevice.objects.filter(office_id__in=selected_offices) if selected_offices else []

        # Фильтрация устройств
        devices = Device.objects.filter(package_id__in=selected_package_devices) if selected_package_devices else Device.objects.all()

        # Получение схем для выбранных офисов
        layouts = OfficeLayout.objects.filter(office_id__in=selected_offices).prefetch_related('device_positions') if selected_offices else []

        # Типы поломок
        breakdown_types = BreakdownType.objects.all()
        breakdown_types_data = [{"id": b.id, "name": b.name} for b in breakdown_types]

        # Проставляем condition_id для пакетов устройств
        package_devices_with_condition = []
        for package_device in package_devices:
            devices_in_package = Device.objects.filter(package_id=package_device.id)
            condition = "1"
            for device in devices_in_package:
                if device.condition_id in [4, 6]:
                    condition = str(device.condition_id)
                    break
            package_devices_with_condition.append({
                "id": package_device.id,
                "number": package_device.number,
                "office_id": package_device.office_id or None,
                "condition_id": condition,
            })

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({
                "bodies": BodySerializer(Body.objects.all(), many=True).data,
                "floors": FloorSerializer(floors, many=True).data,
                "offices": OfficeSerializer(offices, many=True).data,
                "package_devices": package_devices_with_condition,
                "devices": DeviceSerializer(devices, many=True).data,
                "layouts": OfficeLayoutSerializer(layouts, many=True).data,
                "breakdown_types": breakdown_types_data,
            })

    # GET-запрос
    bodies = Body.objects.all()
    floors = Floor.objects.all()
    offices = Office.objects.all()
    return render(request, "body/body_list.html", {
        "bodies": bodies,
        "floors": floors,
        "offices": offices,
        "package_devices": [],
        "devices": [],
        "role": role,
        "notifications_count": notifications_count,
        'active_page': 'body_list'
    })

@swagger_auto_schema(
    method="get",
    operation_summary="Получение списка заявок",
    responses={200: "Успешный ответ"},
)
@swagger_auto_schema(
    method="post",
    operation_summary="Фильтрация заявок",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "selected_schedules": openapi.Schema(
                type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_INTEGER)
            ),
            "selected_packages": openapi.Schema(
                type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_INTEGER)
            ),
            "selected_devices": openapi.Schema(
                type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_INTEGER)
            ),
        },
    ),
    responses={200: "Успешный ответ"},
)
@api_view(["GET", "POST"])
@login_required
def fastapplication_list(request):
    user = request.user
    # Получение роли из первой группы, как в user_dashboard
    groups = user.groups.all()
    role = groups[0].name.lower() if groups.exists() else 'Без роли'
    notifications_count = Application.objects.filter(user=user, status_id=1).count()
    full_name = f"{request.user.last_name} {request.user.first_name}"
    print("Текущее имя пользователя:", full_name)

    moscow_tz = pytz.timezone('Europe/Moscow')
    current_time = datetime.now(moscow_tz)
    current_time_str = current_time.strftime('%H:%M:%S')

    # Получение расписания преподавателя
    teacher_name = f"{request.user.last_name} {request.user.first_name}"
    api_url = f"http://api.bgitu-compass.ru/v2/teacherSearch?teacher={teacher_name}&dateFrom={current_time.date()}&dateTo={current_time.date()}"
    office = None
    filtered_schedule = []

    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            teacher_schedule = response.json()
            for record in teacher_schedule:
                start_time = datetime.strptime(record['startAt'], '%H:%M:%S').time()
                end_time = datetime.strptime(record['endAt'], '%H:%M:%S').time()
                current_time_only = datetime.strptime(current_time_str, '%H:%M:%S').time()
                if start_time <= current_time_only <= end_time:
                    filtered_schedule.append(record)
                    classroom = record['classroom']
                    try:
                        office = Office.objects.get(number=classroom)
                        print(f"ID офиса: {office.id}")
                    except Office.DoesNotExist:
                        print(f"Офис с номером {classroom} не найден в базе.")
        else:
            print(f"Ошибка при запросе расписания преподавателя: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при соединении с API: {e}")

    # Получаем ID офиса
    office_ids = [office.id] if office else []

    if request.method == "POST":
        selected_schedules = list(map(int, request.POST.getlist("selected_schedules", office_ids)))
        selected_packages = list(
            map(int, request.POST.getlist("selected_package_devices", [])))  # Изменено на selected_package_devices
        selected_devices = list(map(int, request.POST.getlist("selected_filtered_devices", [])))

        # Фильтрация офисов
        offices = Office.objects.all()
        if selected_schedules:
            offices = offices.filter(id__in=selected_schedules)

        # Фильтрация пакетов устройств
        package_devices = PackageDevice.objects.filter(office_id__in=selected_schedules or office_ids)
        if selected_packages:
            devices = Device.objects.filter(package_id__in=selected_packages)
        else:
            devices = Device.objects.all()

        # Фильтрация устройств по package_id
        devices = Device.objects.filter(package_id__in=selected_packages) if selected_packages else Device.objects.all()

        # Получаем схемы для выбранных офисов
        layouts = OfficeLayout.objects.filter(office_id__in=selected_schedules or office_ids).prefetch_related(
            'device_positions')

        # Сериализация устройств с package_id
        package_devices_with_condition = []
        for package_device in package_devices:
            devices_in_package = Device.objects.filter(package_id=package_device.id)
            condition = "1"
            for device in devices_in_package:
                if device.condition_id in [4, 6]:
                    condition = str(device.condition_id)
                    break
            package_devices_with_condition.append({
                "id": package_device.id,
                "number": package_device.number,
                "office_id": package_device.office_id or None,
                "condition_id": condition,
                "has_warning": condition == "4"
            })

        breakdown_types = BreakdownType.objects.all()
        breakdown_types_data = [{"id": b.id, "name": b.name} for b in breakdown_types]

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({
                "schedules": filtered_schedule,
                "offices": OfficeSerializer(offices, many=True).data,
                "package_devices": package_devices_with_condition,
                "devices": DeviceSerializer(devices, many=True).data,
                # Убедитесь, что DeviceSerializer включает package_id
                "breakdown_types": breakdown_types_data,
                "layouts": OfficeLayoutSerializer(layouts, many=True).data
            })

    # GET-запрос
    offices = Office.objects.all()
    return render(request, "body/fastapplication_list.html", {
        "schedules": filtered_schedule,
        "package_devices": [],
        "devices": [],
        "breakdown_types": [],
        "layouts": [],
        "offices": offices,
        "role": role,
        "notifications_count": notifications_count,
        'active_page': 'fastapplication_list'
    })


def get_iam_token(oauth_token):
    """Функция для получения IAM-токена из OAuth-токена"""
    url = "https://iam.api.cloud.yandex.net/iam/v1/tokens"
    response = requests.post(url, json={"yandexPassportOauthToken": oauth_token})

    if response.status_code == 200:
        return response.json().get("iamToken")
    else:
        raise Exception(f"IAM-токен не получен: {response.text}")


@csrf_exempt
@swagger_auto_schema(
    method="post",
    operation_summary="Генерация текста с Yandex GPT",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "user_text": openapi.Schema(type=openapi.TYPE_STRING, description="Текст запроса"),
        },
        required=["user_text"],
    ),
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "generated_text": openapi.Schema(type=openapi.TYPE_STRING, description="Сгенерированный текст")
            }
        ),
        400: "Некорректный запрос",
        500: "Ошибка сервера"
    },
)
@api_view(["GET", "POST"])
@login_required  # Требуем аутентификацию
def yagpt_page(request):
    if request.method == "GET":
        user = request.user
        # Получение роли из первой группы, как в user_dashboard
        groups = user.groups.all()
        role = groups[0].name.lower() if groups.exists() else 'Без роли'
        notifications_count = Application.objects.filter(user=user, status_id=1).count()

        context = {'role': role, 'notifications_count': notifications_count, 'active_page': 'ya_index'}
        return render(request, "body/ya_index.html", context)

    elif request.method == "POST":
        user_text = None
        if 'image_file' in request.FILES:
            image_file = request.FILES['image_file']
            image = Image.open(image_file)
            user_text = "Как решить " + pytesseract.image_to_string(image, lang='rus+eng').strip()
            if not user_text:
                return JsonResponse({'error': 'Не удалось распознать текст'}, status=400)
        elif 'user_text' in request.POST:
            user_text = request.POST['user_text'].strip()
        else:
            return JsonResponse({'error': 'Текст не передан'}, status=400)

        try:
            IAM_TOKEN = get_iam_token(OAUTH_TOKEN)  # Предполагается, что функция определена
            response = requests.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                headers={
                    "Authorization": f"Bearer {IAM_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest",  # Предполагается, что FOLDER_ID определен
                    "completionOptions": {"stream": False, "temperature": 0.7},
                    "messages": [
                        {"role": "system",
                         "text": "Ты — опытный компьютерный мастер. Помогай пользователям с компьютерными проблемами, настройками, сборкой ПК и программным обеспечением."},
                        {"role": "user", "text": user_text}
                    ]
                }
            )
            if response.status_code == 200:
                generated_text = response.json()["result"]["alternatives"][0]["message"]["text"]
                truncated_text = generated_text[:850]
                return JsonResponse({'generated_text': truncated_text}, json_dumps_params={"ensure_ascii": False})
            else:
                return JsonResponse({'error': response.text}, status=response.status_code)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@login_required
def user_dashboard(request):
    user = request.user
    groups = user.groups.all()
    role = groups[0].name if groups.exists() else 'Без роли'

    # Определяем, какие заявки отображать и считаем уведомления
    if role == "master":
        # Для мастера: все заявки в системе
        applications = Application.objects.filter(status_id=1).order_by("-data")
        notifications_count = applications.count()  # Уведомления: общее количество всех заявок
        # Сериализация всех заявок
        application_serializer = ApplicationSerializer(applications, many=True)
        application_data = application_serializer.data
        # Группировка заявок по office_number для мастера
        grouped_applications = defaultdict(list)
        for app in application_data:
            grouped_applications[app['office_number']].append(app)
        # Преобразуем в список для шаблона
        grouped_applications_list = [
            {'office_number': office, 'applications': apps}
            for office, apps in grouped_applications.items()
        ]
        # Сортируем по номеру кабинета
        grouped_applications_list = sorted(grouped_applications_list, key=lambda x: x['office_number'])
    else:
        # Для остальных ролей: только заявки текущего пользователя
        applications = Application.objects.filter(user=user, status_id=1)
        notifications_count = applications.count()  # Уведомления: только заявки пользователя
        # Сериализация всех заявок
        application_serializer = ApplicationSerializer(applications, many=True)
        # Передаем данные без группировки
        grouped_applications_list = []  # Пустой список для не-мастеров
        application_data = application_serializer.data

    # Получаем аватар пользователя
    try:
        profile = user.userprofile
        avatar_url = profile.avatar.url if profile.avatar else None
    except UserProfile.DoesNotExist:
        avatar_url = None

    # Отладочная информация
    print(f"Role: {role}, Notifications count: {notifications_count}")

    return render(
        request,
        "body/lkuser.html",
        {
            "user": user,
            "grouped_applications": grouped_applications_list,
            "applications": application_data,
            "notifications_count": notifications_count,
            "role": role,
            "avatar_url": avatar_url,
            'active_page': 'lkuser'
        }
    )


@login_required
def delete_application(request, application_id):
    if request.method == "POST":

        application = get_object_or_404(Application, id=application_id, user=request.user)
        device = get_object_or_404(Device, id=application.device_id)
        device.condition_id = 1  # например, 1 — это "Свободен" или "Работает"
        device.save()
        application.delete()
        return JsonResponse({"message": "Заявка удалена"}, status=200)

    return JsonResponse({"error": "Метод не разрешен"}, status=405)


@swagger_auto_schema(method='post', responses={200: 'Выход выполнен'})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return redirect('login')


class CustomPasswordChangeView(PasswordChangeView):
    template_name = "body/password_change.html"
    success_url = reverse_lazy("lkuser")


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'office_id',
            openapi.IN_QUERY,
            description="ID кабинета для вывода сломанных устройств и типа поломок",
            type=openapi.TYPE_INTEGER,
            required=False
        )
    ],
    responses={200: "Успешно", 400: "Некорректный запрос"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def device_breakdown_stats(request):
    user = request.user
    groups = user.groups.all()
    role = groups[0].name.lower() if groups.exists() else 'Без роли'
    notifications_count = Application.objects.filter(user=user, status_id=1).count()

    office_stats = (
        Application.objects
        .exclude(status__id=3)
        .values("office__id", "office__number", "office__body__number")
        .annotate(broken_count=Count("device"))
    )

    stats_data = [
        {
            "office_id": entry["office__id"],
            "office_number": entry["office__number"],
            "body_number": entry["office__body__number"],
            "broken_count": entry["broken_count"],
        } for entry in office_stats
    ]

    heatmap_raw = (
        Application.objects
        .exclude(status__id=3)
        .annotate(date_only=TruncDate('data'))
        .values('date_only')
        .annotate(count=Count('id'))
        .order_by('date_only')
    )

    heatmap_data = [
        {"date": entry["date_only"].strftime("%Y-%m-%d"), "count": entry["count"]}
        for entry in heatmap_raw
    ]

    if request.GET.get("office_id") and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        office_id = int(request.GET["office_id"])
        broken_devices = (
            Application.objects
            .exclude(status__id=3)
            .filter(office__id=office_id)
            .select_related("device", "office", "breakdown_type")
        )

        breakdown_type_counts = (
            broken_devices
            .values('breakdown_type__name')
            .annotate(count=Count('breakdown_type'))
        )

        breakdown_type_data = [
            {"type": entry["breakdown_type__name"], "count": entry["count"]}
            for entry in breakdown_type_counts
        ]

        broken_serializer = ApplicationSerializer(broken_devices, many=True)

        return JsonResponse({
            "broken_devices": broken_serializer.data,
            "breakdown_type_data": breakdown_type_data,
        })

    return render(request, "body/device_stats.html", {
        "stats_data": stats_data,
        "selected_office": request.GET.get("office_id"),
        "broken_devices": [],
        "chart_data": json.dumps(stats_data),
        "heatmap_data": json.dumps(heatmap_data),
        "breakdown_type_data": json.dumps([]),
        "role": role,
        "notifications_count": notifications_count,
        'active_page': 'device_stats'
    })
