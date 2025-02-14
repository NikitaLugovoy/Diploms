import json
import pytesseract
from PIL import Image
import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

# Укажите путь к исполнимому файлу Tesseract (если необходимо)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Путь для Windows, измените при необходимости

@csrf_exempt  # Отключение проверки CSRF для AJAX-запросов
def yagpt_page(request):
    # URL для Yandex GPT API
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    # IAM-токен и Folder ID
    iam_token = "AQVNxJ5bDf0YdFdVDl9ujKQQhi3T8tZqlN6MENI8"
    folder_id = "b1gca4u7tp73kpmj87no"

    if request.method == "POST":

        user_text = None

        # Проверка на наличие файла в запросе
        if 'image_file' in request.FILES:
            image_file = request.FILES['image_file']
            print(f"Получен файл: {image_file.name}, размер: {image_file.size} байт")  # Выводим информацию о файле

            # Открываем изображение с помощью Pillow
            image = Image.open(image_file)
            # Распознаем текст с изображения с помощью pytesseract для русского и английского языков
            user_text = "Как решить " + pytesseract.image_to_string(image, lang='rus+eng')
            print(f"Текст с изображения: {user_text}")  # Выводим распознанный текст

            if not user_text.strip():  # Если текст не распознан
                return JsonResponse({'error': 'Не удалось распознать текст на изображении'}, status=400)

        elif 'user_text' in request.POST:
            user_text = request.POST['user_text']
            print(f"Получен текст: {user_text}")
        else:
            return JsonResponse({'error': 'Текст не передан'}, status=400)

        # Подготовка данных для Yandex GPT API
        payload = {
            "modelUri": f"gpt://{folder_id}/yandexgpt",
            "completionOptions": {
                "temperature": 0.7,
                "maxTokens": 1000
            },
            "messages": [
                {"role": "system", "text": "Ты — компьютерный мастер, который должен помогать, давать советы и ответы на вопросы."},
                {"role": "user", "text": user_text}
            ]
        }

        headers = {
            "Authorization": f"Api-Key {iam_token}",
            "Content-Type": "application/json",
        }

        try:
            # Запрос к Yandex GPT API
            response = requests.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                # Обработка успешного ответа
                result = response.json()
                generated_text = result.get("result", {}).get("alternatives", [{}])[0].get("message", {}).get("text", "Нет данных")
            else:
                generated_text = f"Ошибка: {response.status_code}"

            # Возврат ответа в формате JSON
            return JsonResponse({'generated_text': generated_text}, json_dumps_params={"ensure_ascii": False})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    # Отображение HTML для GET-запросов
    return render(request, "./yandex/ya_index.html")
