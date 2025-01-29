from django.contrib.auth.models import User
from django.db import models


class Chat(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'chat'

    def __str__(self):
        return self.name


# Таблица сообщений
class Message(models.Model):
    person1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    messenges = models.TextField()
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'  # Указание правильного имени таблицы

    def __str__(self):
        return f"{self.person1}: {self.messenges[:20]}"
