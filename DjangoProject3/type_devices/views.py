from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from .models import TypeDevice
from .forms import TypeDeviceForm

def index(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        action = request.POST.get('action')
        response_data = {"success": False}

        try:
            if action == 'create':
                form = TypeDeviceForm(request.POST)
                if form.is_valid():
                    form.save()
                    response_data["success"] = True

            elif action == 'update':
                device_id = request.POST.get('device_id')
                device = get_object_or_404(TypeDevice, id=device_id)
                form = TypeDeviceForm(request.POST, instance=device)
                if form.is_valid():
                    form.save()
                    response_data["success"] = True

            elif action == 'delete':
                device_id = request.POST.get('device_id')
                device = get_object_or_404(TypeDevice, id=device_id)
                device.delete()
                response_data["success"] = True

            # Возвращаем обновленный список устройств
            devices = TypeDevice.objects.all()
            response_data["devices"] = [{"id": d.id, "name": d.name} for d in devices]
        except Exception as e:
            response_data["error"] = str(e)

        return JsonResponse(response_data)

    # Стандартный рендер страницы
    devices = TypeDevice.objects.all()
    form = TypeDeviceForm()
    return render(request, 'type_devices/index.html', {'devices': devices, 'form': form})
