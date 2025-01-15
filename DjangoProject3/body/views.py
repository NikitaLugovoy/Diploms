from asgiref.sync import sync_to_async
from django.shortcuts import render
from django.http import JsonResponse
from .models import Body, Floor, Office, PackageDevice, Device

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Bot

# Замените 'YOUR_BOT_TOKEN' и 'YOUR_CHAT_ID' на реальные данные вашего бота
BOT_TOKEN = '6176694125:AAFq80IuvhhLNvX_to6yqx_bzeMW3BvecQA'
CHAT_ID = '5006892820'

# Функция отправки сообщения в Telegram

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
                    return JsonResponse({'status': 'error', 'message': f'Устройство с ID {device_id} не найдено!'})

        device_text = (
            f"Устройства: {', '.join(device_serials)}" if device_serials
            else "Устройства не выбраны"
        )

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
        offices = offices.filter(body_id__in=selected_bodies)

    if selected_floors:
        offices = offices.filter(floors_id__in=selected_floors)

    office_data = [
        {
            'id': office.id,
            'number': office.number,
            'floors_id': office.floors_id,
            'body_id': office.body_id,
            'selected': str(office.id) in selected_offices
        }
        for office in offices
    ]

    # Фильтрация пакетов устройств (PackageDevice) только для выбранных офисов
    package_devices = PackageDevice.objects.filter(office_id__in=selected_offices) if selected_offices else []

    # Получаем устройства с учетом их кондиции
    device_data = [
        {'id': device.id, 'number': device.number, 'office_id': device.office_id}
        for device in package_devices
    ]

    # Фильтрация устройств по выбранным пакетам устройств
    devices = Device.objects.all()

    if selected_package_devices:
        devices = Device.objects.filter(package_id__in=selected_package_devices)


    package_devices_with_condition = []
    for package_device in package_devices:
        # Получаем устройства, связанные с этим пакетом
        devices_in_package = Device.objects.filter(package_id=package_device.id)

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
