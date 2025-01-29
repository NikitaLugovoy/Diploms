from asgiref.sync import sync_to_async
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils.timezone import now

from .models import Body, Floor, Office, PackageDevice, Device, Application, Status

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Bot

# Замените 'YOUR_BOT_TOKEN' и 'YOUR_CHAT_ID' на реальные данные вашего бота
BOT_TOKEN = '6176694125:AAFq80IuvhhLNvX_to6yqx_bzeMW3BvecQA'
CHAT_ID = '5006892820'

# Функция отправки сообщения в Telegram

# Код для получения всех заявок
def application_list(request):
    applications = Application.objects.all()

    # Для каждой заявки добавляем номер офиса, серийный номер устройства и имя статуса
    for application in applications:
        # Получаем данные об офисе
        office = Office.objects.get(id=application.office_id)
        application.office_number = office.number

        # Получаем данные о устройстве
        device = Device.objects.get(id=application.device_id)
        application.device_serial_number = device.serial_number

        # Получаем данные о статусе
        status = Status.objects.get(id=application.status_id)
        application.status_name = status.name  # Добавляем имя статуса

    return render(request, 'body/application_list.html', {'applications': applications})


from django.shortcuts import get_object_or_404, redirect
from .models import Application, Device

def close_application(request, application_id):
    # Получаем заявку по ID
    application = get_object_or_404(Application, id=application_id)

    # Обновляем статус заявки на статус с ID = 3
    application.status_id = 3
    application.save()

    # Получаем устройство, связанное с заявкой
    device = get_object_or_404(Device, id=application.device_id)

    # Обновляем condition_id устройства на 1
    device.condition_id = 1
    device.save()

    # После обновления статуса и condition_id перенаправляем обратно на страницу списка заявок
    return redirect('application_list')

@sync_to_async
def save_application(office_id, device_ids, reason):
    """
    Функция для сохранения записей в таблице `applications` для всех выбранных устройств.

    :param office_id: ID офиса.
    :param device_ids: Список ID устройств.
    :param reason: Причина (сообщение).
    :return: JSON-ответ с результатом.
    """
    try:
        application_ids = []
        for device_id in device_ids:
            # Создание новой записи для каждого устройства
            application = Application.objects.create(
                office_id=office_id,
                device_id=device_id,
                reason=reason,
                user_id=1,
                data=now(),  # Текущее время
                status_id=1  # Фиксированное значение
            )
            application.save()
            application_ids.append(application.id)

        return JsonResponse({'status': 'success', 'message': 'Заявки успешно сохранены!', 'application_ids': application_ids})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@sync_to_async
def get_device(device_id):
    try:
        device = Device.objects.get(id=device_id)
        return device
    except Device.DoesNotExist:
        return None

# Функция для
@sync_to_async
def update_device_condition(device):
    device.condition_id = 4
    device.save()


@sync_to_async
def get_body_address(body_id):
    try:
        body = Body.objects.get(id=body_id)
        return body.address
    except Body.DoesNotExist:
        return None

@sync_to_async
def get_office_number(office_id):
    try:
        office = Office.objects.get(id=office_id)
        return office.number
    except Office.DoesNotExist:
        return None


# Функция отправки сообщения в Telegram
@csrf_exempt
async def send_message_to_telegram(request):
    if request.method == 'POST':
        # Получаем сообщение и выбранные данные из запроса
        message = request.POST.get('message', '')
        selected_bodies = request.POST.getlist('selected_bodies', [])
        selected_floors = request.POST.getlist('selected_floors', [])
        selected_offices = request.POST.getlist('selected_offices', [])
        selected_filtered_devices = request.POST.getlist('selected_filtered_devices', [])

        # Получаем адреса корпусов
        body_addresses = []
        for body_id in selected_bodies:
            address = await get_body_address(body_id)
            if address:
                body_addresses.append(address)
            else:
                body_addresses.append(f"Неизвестный корпус (ID: {body_id})")

        # Получаем номера офисов
        # Получаем номера офисов
        office_numbers = []
        for office_id in selected_offices:
            office_number = await get_office_number(office_id)
            if office_number:
                office_numbers.append(str(office_number))  # Преобразование в строку
            else:
                office_numbers.append(f"Неизвестный офис (ID: {office_id})")

        # Формируем текст сообщения
        office_text = (
            f"Офис: {', '.join(office_numbers)}" if office_numbers
            else "Офисы не выбраны"
        )

        # Формируем текст сообщения
        body_text = (
            f"Корпус: {', '.join(body_addresses)}" if body_addresses
            else "Корпуса не выбраны"
        )
        floor_text = f"Этаж: {', '.join(selected_floors)}" if selected_floors else "Этажи не выбраны"

        # Обновляем состояния устройств, если они выбраны
        device_serials = []
        if selected_filtered_devices:
            for device_id in selected_filtered_devices:
                device = await get_device(device_id)
                if device:
                    await update_device_condition(device)
                    device_serials.append(str(device.serial_number))  # Преобразование в строку
                    print(f"Устройство с ID {device_id} изменено, новое condition_id: {device.condition_id}")
                else:
                    device_serials.append(f"Неизвестное устройство (ID: {device_id})")

        device_text = (
            f"Устройства: {', '.join(device_serials)}" if device_serials
            else "Устройства не выбраны"
        )

        # Отправляем сообщение
        # Отправляем сообщение
        if message:
            bot = Bot(token=BOT_TOKEN)
            try:
                # Формируем полный текст сообщения
                formatted_message = (
                    f"Сообщение: {message}\n\n"
                    f"{body_text}\n"
                    f"{floor_text}\n"
                    f"{office_text}\n"
                    f"{device_text}"
                )

                # Отправляем сообщение в Telegram
                await bot.send_message(chat_id=CHAT_ID, text=formatted_message)

                if selected_offices and selected_filtered_devices:
                    office_id = selected_offices[0]  # Используем первый выбранный офис
                    save_response = await save_application(office_id, selected_filtered_devices, message)
                    print(save_response.content)

                return JsonResponse({'status': 'success', 'message': 'Сообщение отправлено!'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
        return JsonResponse({'status': 'error', 'message': 'Сообщение не может быть пустым!'})
    return JsonResponse({'status': 'error', 'message': 'Неверный метод запроса!'})

def body_list(request):
    selected_bodies = request.POST.getlist('selected_bodies', [])
    selected_floors = request.POST.getlist('selected_floors', [])
    selected_filtered_devices = request.POST.getlist('selected_filtered_devices', [])
    selected_offices = request.POST.getlist('selected_offices', [])
    selected_package_devices = request.POST.getlist('selected_package_devices', [])

    print('Selected Bodies:', selected_bodies)
    print('Selected Floors:', selected_floors)
    print('Selected Offices:', selected_offices)
    print('Selected selected_filtered_devices:', selected_filtered_devices)


    # Фильтрация офисов
    offices = Office.objects.all()

    if selected_bodies:
        offices = offices.filter(body__in=selected_bodies)

    if selected_floors:
        offices = offices.filter(floor__in=selected_floors)

    print(offices)

    office_data = [
        {
            'id': office.id,
            'number': office.number,
            'floors_id': office.floor.id,
            'body_id': office.body.id,
            'selected': str(office.id) in selected_offices
        }
        for office in offices
    ]

    print(office_data)

    # Фильтрация пакетов устройств (PackageDevice) только для выбранных офисов
    package_devices = PackageDevice.objects.filter(office__in=selected_offices) if selected_offices else []

    # Получаем устройства с учетом их кондиции
    device_data = [
        {'id': device.id, 'number': device.number, 'office_id': device.office_id}
        for device in package_devices
    ]

    # Фильтрация устройств по выбранным пакетам устройств
    devices = Device.objects.all()

    if selected_package_devices:
        devices = Device.objects.filter(package__in=selected_package_devices)


    package_devices_with_condition = []
    for package_device in package_devices:
        # Получаем устройства, связанные с этим пакетом
        devices_in_package = Device.objects.filter(package=package_device.id)

        # Ищем кондицию устройства, если находим 4 или 6, используем её, иначе 1
        condition = "1"  # По умолчанию кондиция 1
        for device in devices_in_package:
            if device.condition_id in [4, 6]:
                condition = str(device.condition_id)  # Присваиваем кондицию 4 или 6
                break

        # Добавляем в список package_devices с условием
        package_devices_with_condition.append({
            'package_device_id': package_device.id,
            'condition_id': condition
        })

        # Теперь добавим condition_id в сам объект package_device, чтобы передать его в response
        package_device.condition_id = condition

    # Возвращаем данные в формате JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            return JsonResponse({
                'offices': office_data,
                'package_devices': [
                    {
                        'id': package_device.id,
                        'number': package_device.number,
                        'office_id': package_device.office_id,
                        'condition_id': package_device.condition_id,  # Отправляем condition_id как строку
                    }
                    for package_device in package_devices
                ],
                'devices': [
                    {
                        'id': device.id,
                        'serial_number': device.serial_number,
                        'package_id': device.package_id,
                        'condition_id': device.condition_id,  # Отправляем condition_id как строку
                    }
                    for device in devices
                ],
                'package_devices_with_condition': package_devices_with_condition,  # Добавили condition_id в response
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    # Для обычного рендера страницы
    bodies = Body.objects.all()
    floors = Floor.objects.all()

    return render(request, 'body/body_list.html', {
        'bodies': bodies,
        'floors': floors,
        'offices': offices,
        'package_devices': package_devices if selected_offices else [],
        'devices': devices,
        'selected_bodies': selected_bodies,
        'selected_floors': selected_floors,
    })
