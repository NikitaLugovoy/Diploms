from django.contrib import admin

from body.models import Body, Floor, Office, PackageDevice, Device, Application, Status, Schedule, BreakdownType, \
    OfficeLayout, DevicePosition
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
    list_display = ('office', 'device', 'reason', 'data', 'status', 'user', 'breakdown_type')
    search_fields = ('office__number', 'device__serial_number', 'reason', 'breakdown_type__name')

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

@admin.register(BreakdownType)
class BreakdownTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class DevicePositionInline(admin.TabularInline):
    model = DevicePosition
    extra = 1
    fields = ('package_device', 'x', 'y', 'is_active')
    # Если используется django-autocomplete-light, можно включить:
    # autocomplete_fields = ['device']

@admin.register(OfficeLayout)
class OfficeLayoutAdmin(admin.ModelAdmin):
    list_display = ('name', 'office', 'width', 'height', 'created_at')
    list_filter = ('office',)
    search_fields = ('name', 'office__number')
    inlines = [DevicePositionInline]
    fieldsets = (
        (None, {
            'fields': ('office', 'name')
        }),
        ('Размеры сетки', {
            'fields': ('width', 'height')
        }),
    )