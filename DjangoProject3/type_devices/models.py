from django.db import models

# Create your models here.
from django.db import models

class TypeDevice(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'type_devices'  # Явно указываем имя таблицы

    def __str__(self):
        return self.name
