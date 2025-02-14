from django.contrib import admin

from body.models import Body, Floor, Office, PackageDevice, Device, Application, Status, Schedule
from type_devices.models import TypeDevice


# Регистрация моделей
@admin.register(Body)
class BodyAdmin(admin.ModelAdmin):
    list_display = ('number', 'address')
    search_fields = ('number', 'address')

@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ('number',)
    search_fields = ('number',)

# В файле admin.py
@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ('number', 'floor', 'body')  # Заменили floors_id на floor
    search_fields = ('number', 'floor__number', 'body__number')  # Используем связанные поля для поиска


@admin.register(PackageDevice)
class PackageDeviceAdmin(admin.ModelAdmin):
    list_display = ('office_id', 'number')
    search_fields = ('office_id', 'number')

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('type_id', 'serial_number', 'package_id', 'condition_id')
    search_fields = ('serial_number', 'type_id', 'package_id')

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('office_id', 'device_id', 'reason', 'data', 'status_id', 'user_id')
    search_fields = ('office_id', 'device_id', 'reason')

@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(TypeDevice)
class TypeDeviceAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('name', 'office', 'datetime_start', 'datetime_end', 'user')
    search_fields = ('name', 'office__number', 'user__username')