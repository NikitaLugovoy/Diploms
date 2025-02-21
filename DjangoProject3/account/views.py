from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .forms import CustomUserCreationForm
from .serializers import UserSerializer

@swagger_auto_schema(method='post', request_body=UserSerializer, responses={201: 'Регистрация успешна', 400: 'Ошибка регистрации'})
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def register_view(request):
    if request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, "Регистрация успешна! Теперь войдите.")
            return redirect('login')
        else:
            messages.error(request, "Ошибка регистрации. Проверьте введенные данные.")
    return render(request, 'register.html')

@swagger_auto_schema(method='post', request_body=openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'username': openapi.Schema(type=openapi.TYPE_STRING),
        'password': openapi.Schema(type=openapi.TYPE_STRING)
    },
    required=['username', 'password']
), responses={200: 'Успешный вход', 400: 'Ошибка входа'})
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def login_view(request):
    if request.method == 'POST':
        login_form = AuthenticationForm(data=request.POST)
        if login_form.is_valid():
            user = login_form.get_user()
            login(request, user)
            return redirect('success')
        else:
            messages.error(request, "Ошибка входа. Проверьте данные.")
    else:
        login_form = AuthenticationForm()
    return render(request, 'login.html', {'login_form': login_form})

@swagger_auto_schema(method='get', responses={200: 'Успешный вход'})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def success_view(request):
    return render(request, 'success.html', {'username': request.user.username})

@swagger_auto_schema(method='post', responses={200: 'Выход выполнен'})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    messages.success(request, "Вы успешно вышли.")
    return redirect('login')
