from django.urls import path
from . import views
from .views import body_list, send_message_to_telegram, delete_application, CustomPasswordChangeView, logout_view

urlpatterns = [
    path('', views.body_list, name='body_list'),
    path('send-message/', views.send_message_to_telegram, name='send_message_to_telegram'),

    path('yagpt/', views.yagpt_page, name='ya_page'),
    path('application/', views.application_list, name='application_list'),

    path('save-application/', views.save_application, name='save_application'),

    path('fastapplication', views.fastapplication_list, name='fastapplication_list'),

    path('lkuser/', views.user_dashboard, name='lkuser'),
    path("delete_application/<int:application_id>/", delete_application, name="delete_application"),

    path('close_application/<int:application_id>/', views.close_application, name='close_application'),  # Новый путь

    path("add-schedule/", views.add_schedule, name="add_schedule"),

    path("logout/", logout_view, name="logout"),
    path("password_change/", CustomPasswordChangeView.as_view(), name="password_change"),

    path("schedule/list/", views.schedule_list, name="schedule_list"),  # <-- Добавляем маршрут

  ]
