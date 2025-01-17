# views.py
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login,logout
from django.contrib import messages
from .forms import CustomUserCreationForm

def register_view(request):
    if request.method == 'POST':
        reg_form = CustomUserCreationForm(request.POST)
        if reg_form.is_valid():
            reg_form.save()
            messages.success(request, "Регистрация успешна! Теперь войдите.")
            return redirect('login')
        else:
            messages.error(request, "Ошибка регистрации. Проверьте введенные данные.")
    else:
        reg_form = CustomUserCreationForm()
    return render(request, 'register.html', {'reg_form': reg_form})

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

def success_view(request):
    return render(request, 'success.html', {'username': request.user.username})

def logout_view(request):
    logout(request)
    messages.success(request, "Вы успешно вышли.")
    return redirect('login')
