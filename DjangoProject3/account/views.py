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
from django.contrib.auth.models import Group

from django.core.signing import TimestampSigner
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings

signer = TimestampSigner()

from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.core.signing import SignatureExpired, BadSignature
from django.contrib.auth.models import User

def send_activation_email(user, request):
    token = signer.sign(user.pk)
    activation_url = request.build_absolute_uri(
        reverse('activate', kwargs={'token': token})
    )

    subject = 'Подтвердите вашу регистрацию'
    context = {
        'user': user,
        'activation_url': activation_url,
    }

    html_message = render_to_string('email/activation_email.html', context)
    plain_message = render_to_string('email/activation_email.txt', context)

    send_mail(subject, plain_message, settings.EMAIL_HOST_USER, [user.email], html_message=html_message)


@swagger_auto_schema(method='post', request_body=UserSerializer, responses={201: 'Регистрация успешна', 400: 'Ошибка регистрации'})
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def register_view(request):
    reg_form = CustomUserCreationForm()

    if request.method == 'POST':
        reg_form = CustomUserCreationForm(request.POST, request.FILES)
        if reg_form.is_valid():
            user = reg_form.save()  # commit=True по умолчанию
            user.is_active = False  # блокируем доступ до подтверждения
            user.save()

            # Добавление в группу "teacher"
            #teacher_group, created = Group.objects.get_or_create(name='teacher')
            #user.groups.add(teacher_group)

            send_activation_email(user, request)

            messages.success(request, "Регистрация успешна! Проверьте почту для активации аккаунта.")
            return redirect('login')
        else:
            messages.error(request, "Ошибка регистрации. Проверьте введенные данные.")

    return render(request, 'register.html', {'reg_form': reg_form})


@api_view(['GET'])
@permission_classes([AllowAny])
def activate_view(request, token):
    try:
        user_pk = signer.unsign(token, max_age=60*60*24)  # токен живёт 24 часа
        user = User.objects.get(pk=user_pk)
        user.is_active = True
        user.save()
        messages.success(request, "Аккаунт активирован! Теперь вы можете войти.")
        return redirect('login')
    except (SignatureExpired, BadSignature, User.DoesNotExist):
        messages.error(request, "Ссылка недействительна или истекла.")
        return redirect('register')


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
            if not user.is_active:
                messages.error(request, "Ваш аккаунт не активирован. Проверьте почту.")
                return redirect('login')
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
    user = request.user
    groups = user.groups.all()
    role = groups[0].name if groups.exists() else 'Без роли'

    return render(request, 'success.html', {
        'username': user.username,
        'role': role,
    })


@swagger_auto_schema(method='post', responses={200: 'Выход выполнен'})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    messages.success(request, "Вы успешно вышли.")
    return redirect('login')
