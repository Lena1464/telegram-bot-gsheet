import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ========== Telegram Bot ==========

API_TOKEN = 'ТВОЙ_ТОКЕН_ОТ_BOTFATHER'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ========== Google Sheets Setup ==========

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Анкета").sheet1

# ========== States ==========
class Form(StatesGroup):
    name = State()
    phone = State()
    birthdate = State()
    city = State()

# ========== Handlers ==========

@dp.message_handler(commands='start')
async def start(message: types.Message):
    await message.answer("Привет! Давай заполним форму. Как тебя зовут? (ФИО)")
    await Form.name.set()

@dp.message_handler(state=Form.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Теперь введи номер телефона:")
    await Form.phone.set()

@dp.message_handler(state=Form.phone)
async def get_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Дата рождения (например, 01.01.1990):")
    await Form.birthdate.set()

@dp.message_handler(state=Form.birthdate)
async def get_birthdate(message: types.Message, state: FSMContext):
    await state.update_data(birthdate=message.text)
    await message.answer("И наконец, твой город:")
    await Form.city.set()

@dp.message_handler(state=Form.city)
async def get_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    data = await state.get_data()

    # Запись в Google Sheets
    sheet.append_row([data['name'], data['phone'], data['birthdate'], data['city']])
    
    await message.answer("Спасибо! Данные отправлены в таблицу ✅")
    await state.finish()

# ========== Запуск ==========
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
