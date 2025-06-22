import logging
import asyncio
import os
from dotenv import load_dotenv
import django

load_dotenv()  # Загружаем .env в окружение

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DjangoProject3.settings")
django.setup()

from django.conf import settings
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

from body.models import Application, TelegramUser
from django.contrib.auth.models import User

from asgiref.sync import sync_to_async

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = settings.BOT_TOKEN
CHAT_ID = settings.CHAT_ID

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    chat_id = str(message.from_user.id)
    username = message.from_user.username

    await sync_to_async(TelegramUser.objects.get_or_create)(
        chat_id=chat_id,
        defaults={"username": username}
    )

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📋 Заявки"), KeyboardButton(text="❌ Закрыть заявку")]],
        resize_keyboard=True
    )
    await message.answer("Добро пожаловать! Выберите действие:", reply_markup=keyboard)


PAGE_SIZE = 10



async def send_applications_page(message_or_callback, page=1):

    status_id = 1
    offset = (page - 1) * PAGE_SIZE

    total_count = await sync_to_async(lambda: Application.objects.filter(status_id=status_id).count())()

    applications = await sync_to_async(
        lambda: list(
            Application.objects
            .select_related(
                "office", "device__type", "device__package__office__floor", "device__package__office__body", "status", "breakdown_type"
            )
            .filter(status_id=status_id)
            .order_by("-data")[offset:offset + PAGE_SIZE]
        )
    )()

    if not applications:
        text = "Заявок пока нет."
    else:
        pages_count = (total_count + PAGE_SIZE - 1) // PAGE_SIZE
        text = f"Страница {page}/{pages_count}\n"
        for app in applications:
            device = app.device
            device_office = device.package.office
            floor = device_office.floor if device_office else None
            body = device_office.body if device_office else None

            text += (
                f"🆔 Заявка №{app.id}\n"
                f"🛠 Тип устройства: {device.type.name}\n"
                f"🛠 Устройство: {device.serial_number}\n"
                f"📦 Установлено в ПК (пакет): {device.package.number}\n"
                f"🖥 ПК находится в кабинете №{device_office.number if device_office else '—'}\n"
                f"📍 Кабинет расположен на этаже: {floor.number if floor else '—'}\n"
                f"🏢 В корпусе: {body.number if body else '—'}, адрес: {body.address if body else '—'}\n"
                f"⚠️ Тип поломки: {app.breakdown_type.name if app.breakdown_type else '—'}\n"
                f"📅 Дата заявки: {app.data.strftime('%d.%m.%Y %H:%M')}\n"
                f"Статус: {app.status.name}\n\n"
            )

    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"apps_page:{page - 1}"))
    if offset + PAGE_SIZE < total_count:
        buttons.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"apps_page:{page + 1}"))

    if buttons:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons], row_width=2)
    else:
        keyboard = None

    if isinstance(message_or_callback, types.Message):
        await message_or_callback.answer(text, reply_markup=keyboard)
    elif isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.edit_text(text, reply_markup=keyboard)
        await message_or_callback.answer()


@dp.callback_query(lambda c: c.data and c.data.startswith("apps_page:"))
async def process_pagination_callback(callback_query: CallbackQuery):
    page_str = callback_query.data.split(":")[1]
    if page_str.isdigit():
        page = int(page_str)
        await send_applications_page(callback_query, page=page)
    else:
        await callback_query.answer("Некорректный номер страницы", show_alert=True)


@dp.message()
async def handle_text(message: types.Message):
    logger.info(f"Text message received: {message.text} from user {message.from_user.id}")

    if message.text == "📋 Заявки":
        await send_applications_page(message, page=1)

    elif message.text == "❌ Закрыть заявку":
        await message.answer("Введите ID заявки, которую хотите закрыть.")

    elif message.text and message.text.isdigit():
        app_id = int(message.text)
        try:
            application = await sync_to_async(Application.objects.get)(id=app_id)
            application.status_id = 3  # Статус "Закрыто"
            await sync_to_async(application.save)()
            await message.answer(f"Заявка №{app_id} успешно закрыта.")
            logger.info(f"Application {app_id} closed by user {message.from_user.id}")
        except Application.DoesNotExist:
            await message.answer(f"Заявка №{app_id} не найдена.")
            logger.warning(f"Application {app_id} not found when closing by user {message.from_user.id}")

    else:
        # Игнорируем другие сообщения
        pass


async def main():
    logger.info("Starting bot polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
