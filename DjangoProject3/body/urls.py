from django.urls import path
from . import views

urlpatterns = [
    path('', views.body_list, name='body_list'),

]
