from django.urls import path, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from . import views
from .views import body_list, send_message_to_telegram, delete_application, CustomPasswordChangeView, logout_view


schema_view = get_schema_view(
   openapi.Info(
      title="Документация API",
      default_version='v1',
      description="Swagger UI для твоего проекта",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

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

    path("device_stats/", views.device_breakdown_stats, name="device_breakdown_stats"),

    path("schedule/list/", views.schedule_list, name="schedule_list"),  # <-- Добавляем маршрут

    re_path(r'^swagger-ui/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

]
