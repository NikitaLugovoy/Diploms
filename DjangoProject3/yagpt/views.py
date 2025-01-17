import json

import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # Отключение проверки CSRF для AJAX-запросов
def yagpt_page(request):
    # URL для Yandex GPT API
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    # IAM-токен и Folder ID
    iam_token = "AQVNxJ5bDf0YdFdVDl9ujKQQhi3T8tZqlN6MENI8"
    folder_id = "b1gca4u7tp73kpmj87no"

    if request.method == "POST":
        # Получение текста из запроса
        data = json.loads(request.body)
        user_text = data.get("user_text", "")

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
