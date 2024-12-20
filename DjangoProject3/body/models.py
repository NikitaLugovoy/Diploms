from django.db import models

class Body(models.Model):
    number = models.CharField(max_length=50)
    address = models.URLField()

    class Meta:
        db_table = 'body'

    def __str__(self):
        return self.number


from django.db import models

class Floor(models.Model):
    number = models.IntegerField()

    class Meta:
        db_table = 'floors'

    def __str__(self):
        return f"Этаж {self.number}"

from django.db import models

class Office(models.Model):
    number = models.CharField(max_length=50)
    floors_id = models.IntegerField()  # Прямой ID вместо ForeignKey
    body_id = models.IntegerField()   # Прямой ID вместо ForeignKey

    class Meta:
        db_table = 'offices'

    def __str__(self):
        return f"Офис {self.number} (Этаж ID: {self.floors_id}, Корпус ID: {self.body_id})"

class PackageDevice(models.Model):
    office_id = models.IntegerField()  # Связь с моделью Office
    number = models.CharField(max_length=100)  # Номер пакета

    class Meta:
        db_table = 'package_device'

    def __str__(self):
        return f"{self.number} — {self.office_id}"


# Модель для устройств
class Device(models.Model):
    type_id = models.IntegerField()  # Идентификатор типа устройства
    serial_number = models.CharField(max_length=100)  # Серийный номер устройства
    package_id = models.IntegerField()  # Связь с пакетом (PackageDevice)
    condition_id = models.IntegerField()  # Состояние устройства

    class Meta:
        db_table = 'devices'

    def __str__(self):
        return f"Device {self.serial_number} (Type ID: {self.type_id}, Package ID: {self.package_id}, Condition ID: {self.condition_id})"