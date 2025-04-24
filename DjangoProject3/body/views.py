import logging
import json

import pytz
import requests
import telebot
from django.contrib.auth import logout
from django.contrib.auth.views import PasswordChangeView
from django.db.models.functions import TruncDate
from django.urls import reverse_lazy
from pyexpat.errors import messages
from requests.exceptions import RequestException
from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Application, OfficeLayout
from .serializers import ApplicationSerializer, OfficeLayoutSerializer

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .serializers import ApplicationSerializer

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from drf_spectacular.utils import extend_schema

from asgiref.sync import sync_to_async

from .models import (
    Schedule, PackageDevice, Device, Office, Body, Floor, Application, Status, User, BreakdownType
)
from .forms import ScheduleForm
from .serializers import (
    ScheduleSerializer, PackageDeviceSerializer, DeviceSerializer, OfficeSerializer, BodySerializer,
    FastApplicationRequestSerializer, DeviceRequestSerializer, PackageNameRequestSerializer,
    ScheduleNameRequestSerializer, SendMessageSerializer, SendToTelegramSerializer,
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
from django.http import JsonResponse
from django.shortcuts import render
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
    status_id = request.GET.get("status_id")  # Получаем статус из параметров запроса
    applications = Application.objects.select_related("office", "device", "status", "breakdown_type")

    if status_id:
        applications = applications.filter(status_id=status_id)  # Фильтр по статусу

    applications = applications.order_by("-data")  # Сортировка по дате

    serializer = ApplicationSerializer(applications, many=True)

    print("🔹 Полученные данные:", serializer.data)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return Response(serializer.data)

    statuses = Status.objects.all()  # Получаем все статусы для селекта
    return render(request, "body/application_list.html", {
        "applications": serializer.data,
        "statuses": statuses
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
                f"Тип поломки: {breakdown_type.name}\n"
                f"Серийный номер: {device.serial_number}\n"
                f"Пакет: {package.number}\n"
                f"Офис: {office.number}\n"
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
        return JsonResponse({'status': 'success', 'message': 'Сообщение отправлено!'}, status=200)
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в Telegram: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


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
    if request.method == "POST":
        selected_bodies = list(map(int, request.POST.getlist("selected_bodies", [])))
        selected_floors = list(map(int, request.POST.getlist("selected_floors", [])))
        selected_filtered_devices = list(map(int, request.POST.getlist("selected_filtered_devices", [])))
        selected_offices = list(map(int, request.POST.getlist("selected_offices", [])))
        selected_package_devices = list(map(int, request.POST.getlist("selected_package_devices", [])))

        print("Selected Bodies:", selected_bodies)
        print("Selected Floors:", selected_floors)
        print("Selected Offices:", selected_offices)
        print("Selected Filtered Devices:", selected_filtered_devices)

        # Фильтрация офисов
        offices = Office.objects.all()
        if selected_bodies:
            offices = offices.filter(body_id__in=selected_bodies)
        if selected_floors:
            offices = offices.filter(floor_id__in=selected_floors)

        # Фильтрация пакетов устройств
        package_devices = PackageDevice.objects.filter(office_id__in=selected_offices) if selected_offices else []

        # Фильтрация устройств
        devices = Device.objects.filter(
            package_id__in=selected_package_devices) if selected_package_devices else Device.objects.all()

        # Получение схем для выбранных офисов
        layouts = OfficeLayout.objects.filter(office_id__in=selected_offices).prefetch_related(
            'device_positions') if selected_offices else []

        breakdown_types = BreakdownType.objects.all()
        breakdown_types_data = [{"id": b.id, "name": b.name} for b in breakdown_types]

        print("Breakdown Types:", breakdown_types)

        # Проставляем `condition_id` для пакетов устройств
        package_devices_with_condition = []
        for package_device in package_devices:
            devices_in_package = Device.objects.filter(package_id=package_device.id)
            condition = "1"  # По умолчанию
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
                "offices": OfficeSerializer(offices, many=True).data,
                "breakdown_types": breakdown_types_data,
                "package_devices": package_devices_with_condition,
                "devices": DeviceSerializer(devices, many=True).data,
                "layouts": OfficeLayoutSerializer(layouts, many=True).data
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
    full_name = f"{request.user.last_name} {request.user.first_name}"
    print("Текущее имя пользователя:", full_name)

    # Вызов API для получения расписания преподавателя
    teacher_name = f"{request.user.last_name} {request.user.first_name}"

    # Получаем текущую дату

    moscow_tz = pytz.timezone('Europe/Moscow')
    current_time = datetime.now(moscow_tz)

    print("Текущая дата:", current_time)

    # Извлекаем только дату (без времени)
    current_date = current_time.date()

    # Преобразуем текущее время в формат HH:MM:SS
    current_time_str = current_time.strftime('%H:%M:%S')
    office = None
    api_url = f"http://api.bgitu-compass.ru/v2/teacherSearch?teacher={teacher_name}&dateFrom={current_date}&dateTo={current_date}"

    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            teacher_schedule = response.json()
            print(f"Расписание преподавателя {teacher_name}: {teacher_schedule}")
            # Фильтрация записей по времени
            filtered_schedule = []
            for record in teacher_schedule:
                start_time = datetime.strptime(record['startAt'], '%H:%M:%S').time()
                end_time = datetime.strptime(record['endAt'], '%H:%M:%S').time()
                current_time_only = datetime.strptime(current_time_str, '%H:%M:%S').time()

                # Проверяем, попадает ли текущее время в интервал
                if start_time <= current_time_only <= end_time:
                    filtered_schedule.append(record)

            # Выводим отфильтрованные записи
            if filtered_schedule:
                print(f"Отфильтрованное расписание на {current_date}:")
                for item in filtered_schedule:
                    classroom = item['classroom']
                    building = item['building']
                    subject = item['subjectName']
                    group = item['groupName']
                    start = item['startAt']
                    end = item['endAt']

                    print(f"Аудитория {classroom}, корпус {building} — {subject} — {group} ({start}–{end})")

                    # Ищем офис по номеру (номер аудитории = classroom)
                    try:
                        office = Office.objects.get(number=classroom)
                        print(f"ID офиса: {office.id}")
                    except Office.DoesNotExist:
                        print(f"Офис с номером {classroom} не найден в базе.")
            else:
                print("Нет занятий в текущий момент.")
                office = None
        else:
            print(f"Ошибка при запросе расписания преподавателя: {response.status_code}")
            teacher_schedule = []
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при соединении с API: {e}")
        teacher_schedule = []
        office = None

    # Фильтруем расписания для пользователя
    schedules = Schedule.objects.filter(
        user=request.user,
        datetime_start__lte=current_time,
        datetime_end__gte=current_time
    )

    if office is not None:
        office_ids = office.id
    else:
        office_ids = None  # Или другое значение по умолчанию

    print(f"ID офиса: {office_ids}")
    # Получаем переданные параметры (если их нет — пустые списки)
    selected_schedules = list(map(int, request.POST.getlist("selected_schedules", [])))
    selected_packages = list(map(int, request.POST.getlist("selected_packages", [])))
    selected_devices = list(map(int, request.POST.getlist("selected_devices", [])))

    print("Selected Schedules:", selected_schedules)
    print("Selected Packages:", selected_packages)
    print("Selected Devices:", selected_devices)

    package_devices = PackageDevice.objects.filter(office_id__in=[office_ids])

    if selected_packages:
        package_devices = package_devices.filter(id__in=selected_packages)

    devices = Device.objects.filter(package_id__in=selected_packages) if selected_packages else Device.objects.none()

    # Проставляем `condition_id` для пакетов устройств
    package_devices_with_condition = []
    for package_device in package_devices:
        devices_in_package = Device.objects.filter(package_id=package_device.id)
        print(f"Package {package_device.id} содержит устройства: {[device.id for device in devices_in_package]}")

        condition = "1"  # По умолчанию
        for device in devices_in_package:
            print(f"Устройство {device.id} имеет condition_id: {device.condition_id}")
            if device.condition_id in [4, 6]:
                condition = device.condition_id
                print(f"Устройство {device.id} сломано! condition_id = {condition}")
                break

        package_devices_with_condition.append({
            "id": package_device.id,
            "number": package_device.number,
            "office_id": package_device.office_id or None,
            "condition_id": condition,
            "has_warning": condition == 4
        })

    breakdown_types = BreakdownType.objects.all()
    breakdown_types_data = [{"id": b.id, "name": b.name} for b in breakdown_types]

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        package_devices_data = PackageDeviceSerializer(package_devices, many=True).data
        devices_data = DeviceSerializer(devices, many=True).data
        breakdown_types_data = [{"id": b.id, "name": b.name} for b in breakdown_types]

        return JsonResponse({
            "schedules": filtered_schedule,
            "package_devices": package_devices_with_condition,
            "devices": devices_data,
            "breakdown_types": breakdown_types_data
        })

    # Отображение страницы с уже обработанными данными
    return render(request, "body/fastapplication_list.html", {
        "schedules": filtered_schedule,
        "package_devices": package_devices_with_condition,
        "devices": devices,
        "breakdown_types": breakdown_types_data
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
@api_view(["GET", "POST"])  # Теперь поддерживает GET-запросы
def yagpt_page(request):
    if request.method == "GET":
        return render(request, "./body/ya_index.html")  # Возвращаем HTML-страницу

    elif request.method == "POST":
        user_text = None

        # Распознавание текста с изображения
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
            # Получаем IAM-токен
            IAM_TOKEN = get_iam_token(OAUTH_TOKEN)

            # Запрос в Yandex GPT с IAM-токеном
            response = requests.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                headers={
                    "Authorization": f"Bearer {IAM_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest",
                    "completionOptions": {"stream": False, "temperature": 0.7},
                    "messages": [
                        {"role": "system",
                         "text": "Ты — опытный компьютерный мастер. Помогай пользователям с компьютерными проблемами, настройками, сборкой ПК и программным обеспечением."},
                        {"role": "user", "text": user_text}
                    ]
                }
            )

            # Проверка ответа
            if response.status_code == 200:
                generated_text = response.json()["result"]["alternatives"][0]["message"]["text"]
                truncated_text = generated_text[:20]
                return JsonResponse({'generated_text': truncated_text}, json_dumps_params={"ensure_ascii": False})
            else:
                return JsonResponse({'error': response.text}, status=response.status_code)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@login_required
@swagger_auto_schema(
    method='post',
    request_body=ScheduleSerializer,
    responses={201: "Schedule created", 400: "Bad Request"}
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def add_schedule(request):
    offices = Office.objects.all()
    teachers = User.objects.all()

    if request.method == "POST":
        form = ScheduleForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            office_id = form.cleaned_data["office"]
            teacher_id = request.POST.get("teacher")
            datetime_start = form.cleaned_data["datetime_start"]
            datetime_end = form.cleaned_data["datetime_end"]

            if timezone.is_naive(datetime_start):
                datetime_start = timezone.make_aware(datetime_start)
            if timezone.is_naive(datetime_end):
                datetime_end = timezone.make_aware(datetime_end)

            year = datetime_start.year
            limit_date = timezone.make_aware(datetime(year, 6, 30, 23, 59, 59)) if datetime_start.month <= 6 else \
                timezone.make_aware(datetime(year, 12, 31, 23, 59, 59))

            try:
                office = Office.objects.get(id=office_id)
                teacher = User.objects.get(id=teacher_id)
            except (Office.DoesNotExist, User.DoesNotExist):
                return Response({"error": "Invalid office or teacher"}, status=400)

            current_start = datetime_start
            current_end = datetime_end

            while current_start <= limit_date:
                if not Schedule.objects.filter(name=name, office=office, datetime_start=current_start,
                                               datetime_end=current_end, user=teacher).exists():
                    Schedule.objects.create(
                        name=name,
                        office=office,
                        datetime_start=current_start,
                        datetime_end=current_end,
                        user=teacher,
                    )

                current_start += timedelta(weeks=2)
                current_end += timedelta(weeks=2)

            if request.content_type == 'application/json':
                return Response({"message": "Schedule created successfully"}, status=201)
            return redirect("schedule_list")
    else:
        form = ScheduleForm()

    return render(request, "body/add_schedule.html", {"form": form, "offices": offices, "teachers": teachers})


@swagger_auto_schema(
    method='get',
    responses={200: ScheduleSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def schedule_list(request):
    schedules = Schedule.objects.all().order_by("datetime_start")
    if request.content_type == 'application/json':
        serializer = ScheduleSerializer(schedules, many=True)
        return Response(serializer.data, status=200)
    return render(request, "body/schedule_list.html", {"schedules": schedules})


@login_required
def user_dashboard(request):
    user = request.user
    applications = Application.objects.filter(user=user).order_by("-data")

    notifications_count = Application.objects.filter(user=user, status_id=1).count()

    # Сериализация заявок для API-ответа
    application_serializer = ApplicationSerializer(applications, many=True)

    return render(
        request,
        "body/lkuser.html",
        {
            "user": user,
            "applications": application_serializer.data,
            "notifications_count": notifications_count,  # Передаем количество заявок с статусом 1
        }
    )


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Application


@login_required
def delete_application(request, application_id):
    if request.method == "POST":
        application = get_object_or_404(Application, id=application_id, user=request.user)
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
    success_url = reverse_lazy("user_dashboard")


from django.db.models import Count
from django.http import JsonResponse


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
    # Получаем общую статистику
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

    # Если это AJAX-запрос — вернуть JSON
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

    # Иначе вернуть обычную HTML-страницу
    return render(request, "body/device_stats.html", {
        "stats_data": stats_data,
        "selected_office": request.GET.get("office_id"),
        "broken_devices": [],
        "chart_data": json.dumps(stats_data),
        "heatmap_data": json.dumps(heatmap_data),
        "breakdown_type_data": json.dumps([]),
    })
