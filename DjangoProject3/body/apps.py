from django.apps import AppConfig


class BodyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'body'  # Указываем имя вашего приложения


    def ready(self):
        import body.signals