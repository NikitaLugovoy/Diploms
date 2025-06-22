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

class DeviceInline(admin.TabularInline):
    model = Device
    extra = 4
    fields = ('type', 'serial_number', 'condition')

# В файле admin.py
@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ('number', 'floor', 'body')
    search_fields = ('number', 'floor__number', 'body__number')

@admin.register(PackageDevice)
class PackageDeviceAdmin(admin.ModelAdmin):
    list_display = ('office', 'number' )
    search_fields = ('office__number', 'number')
    inlines = [DeviceInline]

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('get_type_name', 'serial_number', 'package_id', 'get_condition_name')
    search_fields = ('serial_number', 'type__name', 'package__number', 'condition__name')
    def get_condition_name(self, obj):
        return obj.condition.name
    get_condition_name.short_description = 'Состояние'
    def get_type_name(self, obj):
        return obj.type.name  # Предполагается, что поле называется `type` и ссылается на модель TypeDevice
    get_type_name.short_description = 'Тип устройства'

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

