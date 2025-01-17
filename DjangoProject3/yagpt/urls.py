from django.urls import path
from . import views

urlpatterns = [
    path('', views.yagpt_page, name='ya_index'),
    path('yagpt/', views.yagpt_page, name='ya_page'),
  ]
