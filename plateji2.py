import sqlite3
from aiogram import executor, types, Bot, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ContentType
from yookassa import Configuration, Payment
import logging

# Установите ключи API YooKassa
Configuration.secret_key = "test_LHZk1hQgcw3Tl88kZiyn1rGGrT-KD7uFrQ0zKXOOm6M"
Configuration.account_id = 367606
API_TOKEN = '7131520342:AAG0oqDH-4Uuboj9YXZxyhFO_fA3sWC_6Q0'

conn = sqlite3.connect('subscribers.db')
cursor = conn.cursor()

# Создайте таблицу подписчиков, если она не существует
cursor.execute('''
CREATE TABLE IF NOT EXISTS subscribers (
    id INTEGER PRIMARY KEY,
    username TEXT, 
    subscription_date TIMESTAMP
)
''')
conn.commit()

logging.basicConfig(level=logging.INFO)
subscribers = []
admins = []

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Создание кнопок для интерфейса
keyboard = InlineKeyboardMarkup()
btn_payment = InlineKeyboardButton('Оплатить', callback_data='payment')
btn_cancel = InlineKeyboardButton('Отмена', callback_data='cancel')
keyboard.add(btn_payment, btn_cancel)

keyboard_check = InlineKeyboardMarkup()
btn_check = InlineKeyboardButton('Проверить подписку', callback_data='check')
keyboard_check.add(btn_check)


@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    id = str(message.from_user.id)
    if id in subscribers or id in admins:
        username = message.from_user.username
        await message.answer(f'Добро пожаловать {username}')
    else:
        await message.answer('Для начала работы вам необходимо подписаться', reply_markup=keyboard)



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)