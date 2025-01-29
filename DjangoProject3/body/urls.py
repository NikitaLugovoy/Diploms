from django.urls import path
from . import views
from .views import body_list, send_message_to_telegram

urlpatterns = [
    path('', views.body_list, name='body_list'),
    path('send-message/', views.send_message_to_telegram, name='send_message_to_telegram'),

    path('application', views.application_list, name='application_list'),

path('close_application/<int:application_id>/', views.close_application, name='close_application'),  # Новый путь
  ]
