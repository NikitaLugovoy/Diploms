from django.contrib.auth.models import User
from django.db import models


class Body(models.Model):
    number = models.CharField(max_length=50)
    address = models.CharField(max_length=50)

    class Meta:
        db_table = 'body'

    def __str__(self):
        return f"{self.number} {self.address}"


class Floor(models.Model):
    number = models.IntegerField()

    class Meta:
        db_table = 'floors'

    def __str__(self):
        return f"Этаж {self.number} ({self.number})"


class Office(models.Model):
    number = models.CharField(max_length=50)
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE)
    body = models.ForeignKey(Body, on_delete=models.CASCADE)

    class Meta:
        db_table = 'offices'

    def __str__(self):
        return f"Офис {self.number} (Этаж: {self.floor.number}, Корпус: {self.body.number})"


class BreakdownType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'breakdown_types'

    def __str__(self):
        return self.name


class PackageDevice(models.Model):
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='package_devices')
    number = models.CharField(max_length=100)

    class Meta:
        db_table = 'package_device'

    def __str__(self):
        return f"{self.number} — {self.office.number}"


class Device(models.Model):
    type = models.ForeignKey('type_devices.TypeDevice', on_delete=models.CASCADE, related_name='devices')
    serial_number = models.CharField(max_length=100)
    package = models.ForeignKey(PackageDevice, on_delete=models.CASCADE, related_name='devices')
    condition = models.ForeignKey('Status', on_delete=models.CASCADE, related_name='devices')

    class Meta:
        db_table = 'devices'

    def __str__(self):
        return f"Device {self.serial_number} (Type ID: {self.type.name}, Package: {self.package.number}, Condition: {self.condition.name})"


class Application(models.Model):
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='applications')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='applications')
    reason = models.TextField()
    data = models.DateTimeField(auto_now_add=True)
    status = models.ForeignKey('Status', on_delete=models.CASCADE, related_name='applications')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    breakdown_type = models.ForeignKey(BreakdownType, on_delete=models.CASCADE, related_name='applications', null=True,
                                       blank=True)

    class Meta:
        db_table = 'applications'

    def __str__(self):
        return f"Application {self.id} (Office: {self.office.number}, Device: {self.device.serial_number})"


class Status(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'statuses'

    def __str__(self):
        return self.name


class Schedule(models.Model):
    name = models.TextField()
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='schedules')
    datetime_start = models.DateTimeField()
    datetime_end = models.DateTimeField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedules')

    class Meta:
        db_table = 'schedules'

    def __str__(self):
        return self.name


class OfficeLayout(models.Model):
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='layouts')
    name = models.CharField(max_length=255)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.office})"


class DevicePosition(models.Model):
    layout = models.ForeignKey(OfficeLayout, on_delete=models.CASCADE, related_name='device_positions')
    package_device = models.ForeignKey(PackageDevice, on_delete=models.CASCADE,
                                       related_name='positions')  # Изменено с device на package_device
    x = models.PositiveIntegerField()
    y = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.package_device} at ({self.x}, {self.y})"
