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
API_TOKEN = "8091593417:AAEKe5qIJLiLslk05Ssjk5tfUD-aCiDYKRE"
if not API_TOKEN:
    raise ValueError("❌ Переменная API_TOKEN не установлена!")

print("TOKEN:", API_TOKEN)
if not API_TOKEN:
    raise ValueError("❌ API_TOKEN is not set!")

print("TOKEN IS:", API_TOKEN)


bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ==== НАСТРОЙКИ GOOGLE SHEETS ====
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_path = "/etc/secrets/credentials.json"  # путь для Render Secret File

if not os.path.exists(creds_path):
    raise FileNotFoundError(f"❌ Файл {creds_path} не найден. Убедись, что он загружен в Secret Files!")

creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
client = gspread.authorize(creds)
sheet = client.open("Анкета").sheet1

# ==== СОСТОЯНИЯ ====
class Form(StatesGroup):
    name = State()
    phone = State()
    birthdate = State()
    city = State()

# ==== СТАРТ ====
@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    await Form.name.set()
    await message.reply("Привет! Давай начнём. Введи своё ФИО:")

# ==== ОБРАБОТКА ФИО ====
@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await Form.phone.set()
    await message.reply("Теперь введи номер телефона:")

# ==== ОБРАБОТКА ТЕЛЕФОНА ====
@dp.message_handler(state=Form.phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await Form.birthdate.set()
    await message.reply("Укажи дату рождения (например: 01.01.1990):")

# ==== ОБРАБОТКА ДАТЫ ====
@dp.message_handler(state=Form.birthdate)
async def process_birthdate(message: types.Message, state: FSMContext):
    await state.update_data(birthdate=message.text)
    await Form.city.set()
    await message.reply("И, наконец, город проживания:")

# ==== ОБРАБОТКА ГОРОДА И ЗАПИСЬ ====
@dp.message_handler(state=Form.city)
async def process_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    data = await state.get_data()

    # Пытаемся записать в таблицу
    try:
        sheet.append_row([data['name'], data['phone'], data['birthdate'], data['city']])
        await message.reply("🎉 Спасибо! Данные успешно записаны в Google Sheets.")
    except Exception as e:
        await message.reply("⚠️ Произошла ошибка при записи в таблицу.")
        logging.error(f"Ошибка при записи в Google Sheets: {e}")

    await state.finish()

# ==== ЗАПУСК ====
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
