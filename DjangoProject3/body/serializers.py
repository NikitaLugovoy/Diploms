from rest_framework import serializers
from .models import (
    Application, Device, Office, Status, PackageDevice, Body, Floor, Schedule
)


class BodySerializer(serializers.ModelSerializer):
    class Meta:
        model = Body
        fields = ["id", "number", "address"]


class FloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = ["id", "number"]


class OfficeSerializer(serializers.ModelSerializer):
    floor_id = serializers.IntegerField(source="floor.id", read_only=True)
    body_id = serializers.IntegerField(source="body.id", read_only=True)

    class Meta:
        model = Office
        fields = ["id", "number", "floor_id", "body_id"]


class PackageDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageDevice
        fields = ["id", "number", "office_id"]


class DeviceSerializer(serializers.ModelSerializer):
    package_id = serializers.IntegerField(source="package.id", read_only=True)
    condition_id = serializers.IntegerField(source="condition.id", read_only=True)

    class Meta:
        model = Device
        fields = ["id", "serial_number", "package_id", "condition_id"]


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = ["id", "name"]


class ApplicationSerializer(serializers.ModelSerializer):
    office_number = serializers.CharField(source='office.number', read_only=True)
    floor_number = serializers.IntegerField(source='office.floor.number', read_only=True)
    body_number = serializers.CharField(source='office.body.number', read_only=True)
    device_serial_number = serializers.CharField(source='device.serial_number', read_only=True)
    status_name = serializers.CharField(source='status.name', read_only=True)
    status_id = serializers.IntegerField(source='status.id', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'office_number', 'floor_number', 'body_number',
            'device_serial_number', 'reason', 'data', 'status_name', 'status_id', 'user_id'
        ]


class ScheduleSerializer(serializers.ModelSerializer):
    office = OfficeSerializer(read_only=True)

    class Meta:
        model = Schedule
        fields = ["id", "name", "office", "datetime_start", "datetime_end", "user_id"]


# **Сериализаторы для обработки данных API**
class CloseApplicationSerializer(serializers.Serializer):
    application_id = serializers.IntegerField()


class SaveApplicationSerializer(serializers.Serializer):
    office_id = serializers.IntegerField()
    device_ids = serializers.ListField(child=serializers.IntegerField())
    reason = serializers.CharField(max_length=255)

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
