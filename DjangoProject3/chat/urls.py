from django.urls import path
from . import views

urlpatterns = [
    path('chat/<int:chat_id>/', views.chat_page, name='chat_index'),  # Страница чата
    path('chat/<int:chat_id>/send/', views.send_message, name='send_message'),  # Отправка сообщения
]
