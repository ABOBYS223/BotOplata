import sqlite3
from datetime import datetime
from aiogram import executor, types, Bot, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ContentType
from yookassa import Configuration, Payment
from config import TOKEN_PAY, secret_k_test, acc_id_test
import logging
from aiohttp import web

TOKEN = TOKEN_PAY
# Установите ключи API YooKassa
Configuration.secret_key = secret_k_test
Configuration.account_id = acc_id_test
API_TOKEN = TOKEN

# Создайте подключение к базе данных SQLite
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

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Список подписчиков и список админов
subscribers = []
admins = []  # Замените 'id' на фактические ID ваших администраторов

# Создание объектов бота и диспетчера
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


@dp.message_handler(commands=['help'])
async def help_message(message: types.Message):
    await message.answer('Вы находитесь в информационном боте\n'
                         'Для взаимодействия с ботом необходима подписка\n'
                         'Если вы оформили подписку и она не активна, напишите'
                         'пожалуйста администраторам @логин', reply_markup=keyboard_check)

@dp.callback_query_handler(text='cancel')
async def push_cancel(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer('Вы отказались от подписки\nДля дальнейшей работы с ботом необходима подписка')


@dp.callback_query_handler(text='payment')
async def payment(callback: types.CallbackQuery):
    await callback.answer()
    podpischik_id = str(callback.from_user.id)
    # Создайте объект платежа в YooKassa
    payment = Payment.create({
        "amount": {
            "value": "10.00",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://www.eremingroup.ru/webhook.php"
        },
        "capture": True,
        "description": podpischik_id
    })

    # Отправьте ссылку на оплату пользователю
    payment_url = payment.confirmation.confirmation_url
    await bot.send_message(callback.from_user.id, f'Для оплаты подписки перейдите по ссылке: {payment_url}')


@dp.callback_query_handler(text='check')
async def check_sub(callback: types.CallbackQuery):
    await callback.answer()
    id = str(callback.from_user.id)
    if id in admins:
        await callback.message.answer('Вы являетесь администратором')
    elif id in subscribers:
        await callback.message.answer('Подписка активирована')
    else:
        await callback.message.answer('Подписка не активна', reply_markup=keyboard)




async def handle_payment_notification(request):
    data = await request.json()

    # Логируем полученные данные
    logging.info(f'Received payment notification data: {data}')

    payment_status = data.get('status')

    if payment_status == 'succeeded':
        order_id = data.get('id')  # Получаем идентификатор платежа
        user_id = data.get('user_id')  # Получаем идентификатор пользователя (если такая информация доступна)

        # Ваш код для обработки успешного платежа здесь
        # Например, добавление пользователя в базу данных и отправка сообщения

        if user_id:
            conn = sqlite3.connect('subscribers.db')
            cursor = conn.cursor()
            user_id_str = str(user_id)
            cursor.execute("SELECT * FROM subscribers WHERE id=?", (user_id_str,))
            existing_user = cursor.fetchone()
            conn.close()

            if not existing_user:
                username = data.get('metadata', {}).get('username')  # Получаем имя пользователя из метаданных (если доступно)
                if not username:
                    username = f'User_{user_id}'  # Используем "User_ID" в качестве имени, если нет метаданных
                subscription_date = datetime.now()

                # Добавляем пользователя в базу данных
                conn = sqlite3.connect('subscribers.db')
                cursor = conn.cursor()
                cursor.execute("INSERT INTO subscribers (id, username, subscription_date) VALUES (?, ?, ?)",
                               (user_id_str, username, subscription_date))
                conn.commit()
                conn.close()

                # Отправляем сообщение о успешной подписке
                bot = Bot(token=API_TOKEN)
                await bot.send_message(user_id, 'Вы успешно подписались!')

        # Отправьте ответ серверу YooKassa (HTTP 200 OK), чтобы подтвердить получение уведомления
        logging.info(f'Successful payment received. Order ID: {order_id}, User ID: {user_id}')
        return web.Response(status=200)

    else:
        # Платеж не выполнен или выполнен с ошибкой, обработайте его соответствующим образом
        # Например, отправьте уведомление об ошибке

        # Отправьте ответ серверу YooKassa (HTTP 200 OK), чтобы подтвердить получение уведомления
        logging.error(f'Payment notification error. Status: {payment_status}')
        return web.Response(status=200)


app = web.Application()
app.router.add_post('/payment_notification', handle_payment_notification)



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
