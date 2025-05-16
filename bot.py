import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import logging

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==== ЛОГИ ====
logging.basicConfig(level=logging.INFO)

# ==== НАСТРОЙКИ ====
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise ValueError("❌ Переменная API_TOKEN не установлена!")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ==== GOOGLE SHEETS ====
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_path = "/etc/secrets/credentials.json"

if not os.path.exists(creds_path):
    raise FileNotFoundError(f"❌ Файл {creds_path} не найден. Убедись, что он загружен в Secret Files!")

creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
client = gspread.authorize(creds)
sheet = client.open("Анкета").sheet1

# ==== СОСТОЯНИЯ ====
class Form(StatesGroup):
    name = State()
    birthdate = State()
    phone = State()

# ==== КНОПКИ МЕНЮ ====
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

main_menu = InlineKeyboardMarkup(row_width=1)
main_menu.add(
    InlineKeyboardButton("🪪 Оформить бонусную карту", callback_data="start_form"),
    InlineKeyboardButton("📍 Салоны рядом", url="https://taplink.cc/vyberi_gorod"),
    InlineKeyboardButton("👁 Заказать линзы", url="https://www.optica-chameleon.ru/catalog/lenses/?sort=hit"),
    InlineKeyboardButton("🛍 Посмотреть каталог", url="https://www.optica-chameleon.ru/"),
    InlineKeyboardButton("💬 Написать в WhatsApp", url="https://wtsp.cc/89841425515")
)

# ==== СТАРТ ====
@dp.message_handler(commands='start', state="*")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "👋 Привет! Я бот сети оптик ХАМЕЛЕОН.\nЯ помогу тебе оформить бонусную карту и не только!\n\nВыбери нужное действие:",
        reply_markup=main_menu
    )

# ==== ОБРАБОТКА КНОПКИ АНКЕТЫ ====
@dp.callback_query_handler(lambda c: c.data == "start_form")
async def process_start_button(callback_query: types.CallbackQuery):
    await Form.name.set()
    await bot.send_message(callback_query.from_user.id, "✍️ Введите ваше ФИО (например: Иванов Иван Иванович):")

# ==== ФИО ====
@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await Form.birthdate.set()
    await message.reply("📅 Укажите дату рождения (в формате: 01.01.1990):")

# ==== ДАТА РОЖДЕНИЯ ====
@dp.message_handler(state=Form.birthdate)
async def process_birthdate(message: types.Message, state: FSMContext):
    await state.update_data(birthdate=message.text)
    await Form.phone.set()
    await message.reply("📞 Введите номер телефона (только цифры):")

# ==== ТЕЛЕФОН + ЗАПИСЬ ====
@dp.message_handler(state=Form.phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    data = await state.get_data()

    try:
        sheet.append_row([data['name'], data['phone'], data['birthdate']])
    except Exception as e:
        await message.reply("⚠️ Произошла ошибка при записи в таблицу.")
        logging.error(f"Ошибка при записи в Google Sheets: {e}")
        await state.finish()
        return

    await state.finish()
    await message.reply(
        "🎉 Отличная работа!\n\n🪪 Ваша бонусная карта будет создана в ближайшее время и активируется автоматически.\n📞 Просто назовите ваш номер телефона в любом салоне ХАМЕЛЕОН."
    )

# ==== ЗАПУСК ====
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
