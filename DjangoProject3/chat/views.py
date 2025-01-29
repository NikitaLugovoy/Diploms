from django.shortcuts import render, get_object_or_404
from .models import Chat, Message, User


def chat_page(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    messages = Message.objects.filter(chat=chat).order_by('time')  # Сообщения по времени
    context = {
        'chat': chat,
        'messages': messages,
    }
    return render(request, 'chat_index.html', context)

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect

@csrf_exempt
def send_message(request, chat_id):
    if request.method == 'POST':
        chat = get_object_or_404(Chat, id=chat_id)
        person1 = request.user
        message_text = request.POST.get('messenges')

        if not message_text:
            return redirect('chat_index', chat_id=chat_id)

        # Создание сообщения
        Message.objects.create(person1=person1, chat=chat, messenges=message_text)
        return redirect('chat_index', chat_id=chat_id)