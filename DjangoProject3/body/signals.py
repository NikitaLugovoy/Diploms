# body/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PackageDevice, Device
from type_devices.models import TypeDevice
from .models import Status


@receiver(post_save, sender=PackageDevice)
def create_default_devices(sender, instance, created, **kwargs):
    if created:
        device_type_ids = [6, 5, 2, 1]
        default_condition_id = 2  # Можно также получить через Status.objects.get(name='...')

        for type_id in device_type_ids:
            try:
                device_type = TypeDevice.objects.get(id=type_id)
                Device.objects.create(
                    type=device_type,
                    serial_number="-",
                    package=instance,
                    condition_id=default_condition_id
                )
            except TypeDevice.DoesNotExist:
                print(f"TypeDevice с id={type_id} не найден")
