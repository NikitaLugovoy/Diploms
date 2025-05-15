from rest_framework import serializers
from .models import (
    Application, Device, Office, Status, PackageDevice, Body, Floor, Schedule, BreakdownType, DevicePosition,
    OfficeLayout
)


class BodySerializer(serializers.ModelSerializer):
    class Meta:
        model = Body
        fields = ["id", "number", "address"]


class FloorSerializer(serializers.ModelSerializer):
    body_ids = serializers.PrimaryKeyRelatedField(
        source='bodies', many=True, read_only=True
    )

    class Meta:
        model = Floor
        fields = ["id", "number", "body_ids"]


class OfficeSerializer(serializers.ModelSerializer):
    floor_id = serializers.IntegerField(source="floor.id", read_only=True)
    body_id = serializers.IntegerField(source="body.id", read_only=True)
    floor_number = serializers.IntegerField(source="floor.number", read_only=True)

    class Meta:
        model = Office
        fields = ["id", "number", "floor_id", "body_id", "floor_number"]

class PackageDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageDevice
        fields = ["id", "number", "office_id"]


class DeviceSerializer(serializers.ModelSerializer):
    package_id = serializers.IntegerField(source="package.id", read_only=True)
    condition_id = serializers.IntegerField(source="condition.id", read_only=True)
    type_name = serializers.CharField(source="type.name", read_only=True)
    class Meta:
        model = Device
        fields = ["id", "serial_number", "package_id", "condition_id", "type_name"]


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = ["id", "name"]


class ApplicationSerializer(serializers.ModelSerializer):
    office_number = serializers.CharField(source='office.number', read_only=True)
    floor_number = serializers.IntegerField(source='office.floor.number', read_only=True)
    body_number = serializers.CharField(source='office.body.number', read_only=True)
    device_serial_number = serializers.CharField(source='device.serial_number', read_only=True)
    package_id = serializers.IntegerField(source="device.package.id", read_only=True)
    status_name = serializers.CharField(source='status.name', read_only=True)
    status_id = serializers.IntegerField(source='status.id', read_only=True)
    breakdown_type_id = serializers.IntegerField(source='breakdown_type.id', read_only=True, allow_null=True)
    breakdown_type_name = serializers.CharField(source='breakdown_type.name', read_only=True, allow_null=True)
    user_name = serializers.CharField(source='user.username', read_only=True)  # Добавляем имя пользователя

    def get_breakdown_type_id(self, obj):
        return obj.breakdown_type.id if obj.breakdown_type else None

    def get_breakdown_type_name(self, obj):
        return obj.breakdown_type.name if obj.breakdown_type else "Не указано"

    class Meta:
        model = Application
        fields = "__all__"


class ScheduleSerializer(serializers.ModelSerializer):
    office = OfficeSerializer(read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Schedule
        fields = ["id", "name", "office", "datetime_start", "datetime_end", "user_id", "user_name"]


# **Сериализаторы для обработки данных API**
class CloseApplicationSerializer(serializers.Serializer):
    application_id = serializers.IntegerField()


class SaveApplicationSerializer(serializers.Serializer):
    office_id = serializers.IntegerField()
    device_ids = serializers.ListField(child=serializers.IntegerField())
    reason = serializers.CharField(max_length=255)
    breakdown_type_id = serializers.IntegerField(required=False, allow_null=True)
    user_id = serializers.IntegerField(required=False)


class SendMessageSerializer(serializers.Serializer):
    message = serializers.CharField()
    selected_filtered_devices = serializers.ListField(
        child=serializers.IntegerField()
    )


class FastApplicationRequestSerializer(serializers.Serializer):
    selected_schedules = serializers.ListField(child=serializers.IntegerField(), required=False)
    selected_packages = serializers.ListField(child=serializers.IntegerField(), required=False)
    selected_devices = serializers.ListField(child=serializers.IntegerField(), required=False)


class SendToTelegramSerializer(serializers.Serializer):
    message = serializers.CharField()
    all_schedules = serializers.ListField(child=serializers.IntegerField(), required=False, default=[])
    all_offices = serializers.ListField(child=serializers.IntegerField(), required=False, default=[])
    selected_packages = serializers.ListField(child=serializers.IntegerField(), required=False, default=[])
    selected_devices = serializers.ListField(child=serializers.IntegerField(), required=False, default=[])


from rest_framework import serializers


class ScheduleNameRequestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)


class PackageNameRequestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)


class DeviceRequestSerializer(serializers.Serializer):
    device_id = serializers.IntegerField()


class BreakdownTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BreakdownType
        fields = ["id", "name"]


class DevicePositionSerializer(serializers.ModelSerializer):
    package_device_id = serializers.IntegerField(source='package_device.id')
    number = serializers.CharField(source='package_device.number')

    class Meta:
        model = DevicePosition
        fields = ['id', 'package_device_id', 'number', 'x', 'y', 'is_active']


class OfficeLayoutSerializer(serializers.ModelSerializer):
    device_positions = DevicePositionSerializer(many=True, read_only=True)
    office_id = serializers.IntegerField(source='office.id')

    class Meta:
        model = OfficeLayout
        fields = ['id', 'name', 'office_id', 'width', 'height', 'device_positions']
