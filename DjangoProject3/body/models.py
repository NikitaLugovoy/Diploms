from django.contrib.auth.models import User
from django.db import models

class Body(models.Model):
    number = models.CharField(max_length=50, db_index=True)
    address = models.CharField(max_length=50)

    class Meta:
        db_table = 'body'

    def __str__(self):
        return f"{self.number}"

class Floor(models.Model):
    number = models.IntegerField(db_index=True)
    bodies = models.ManyToManyField(Body, related_name='floors')

    class Meta:
        db_table = 'floors'

    def __str__(self):
        return f"{self.number}"

class Office(models.Model):
    number = models.CharField(max_length=50, db_index=True)
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, db_index=True)
    body = models.ForeignKey(Body, on_delete=models.CASCADE, db_index=True)

    class Meta:
        db_table = 'offices'
        indexes = [
            models.Index(fields=['floor', 'body']),
        ]

    def __str__(self):
        return f"{self.number}"


class BreakdownType(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)

    class Meta:
        db_table = 'breakdown_types'

    def __str__(self):
        return f"{self.name}"


class PackageDevice(models.Model):
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='package_devices', db_index=True)
    number = models.CharField(max_length=100, db_index=True)

    class Meta:
        db_table = 'package_device'

    def __str__(self):
        return f"{self.number}"


class Device(models.Model):
    type = models.ForeignKey('type_devices.TypeDevice', on_delete=models.CASCADE, related_name='devices', db_index=True)
    serial_number = models.CharField(max_length=100, db_index=True)
    package = models.ForeignKey(PackageDevice, on_delete=models.CASCADE, related_name='devices', db_index=True)
    condition = models.ForeignKey('Status', on_delete=models.CASCADE, related_name='devices', db_index=True)

    class Meta:
        db_table = 'devices'
        indexes = [
            models.Index(fields=['type', 'serial_number']),
        ]

    def __str__(self):
        return f"{self.type}, {self.condition.name}"

class Application(models.Model):
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='applications', db_index=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='applications', db_index=True)
    reason = models.TextField()
    data = models.DateTimeField(auto_now_add=True, db_index=True)
    status = models.ForeignKey('Status', on_delete=models.CASCADE, related_name='applications', db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications', db_index=True)
    breakdown_type = models.ForeignKey(BreakdownType, on_delete=models.CASCADE, related_name='applications', null=True, blank=True, db_index=True)

    class Meta:
        db_table = 'applications'
        indexes = [
            models.Index(fields=['data']),
            models.Index(fields=['office', 'status']),
        ]


class Status(models.Model):
    name = models.CharField(max_length=100, db_index=True)

    class Meta:
        db_table = 'statuses'

    def __str__(self):
        return f"{self.name}"

class Schedule(models.Model):
    name = models.TextField()
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='schedules', db_index=True)
    datetime_start = models.DateTimeField(db_index=True)
    datetime_end = models.DateTimeField(db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedules', db_index=True)

    class Meta:
        db_table = 'schedules'
        indexes = [
            models.Index(fields=['datetime_start', 'datetime_end']),
        ]


class OfficeLayout(models.Model):
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='layouts', db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['office', 'created_at']),
        ]

        def __str__(self):
            return f"{self.name} / {self.office.number}"


class DevicePosition(models.Model):
    layout = models.ForeignKey(OfficeLayout, on_delete=models.CASCADE, related_name='device_positions', db_index=True)
    package_device = models.ForeignKey(PackageDevice, on_delete=models.CASCADE, related_name='positions', db_index=True)
    x = models.PositiveIntegerField()
    y = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['layout', 'package_device']),
        ]

class TelegramUser(models.Model):
    chat_id = models.CharField(max_length=50, unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
