from aiogram import executor, types, Bot
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ContentType
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import BOT_TOKEN, UKASSA_TOKEN, ADMINS

API_TOKEN = "7131520342:AAG0oqDH-4Uuboj9YXZxyhFO_fA3sWC_6Q0"
UKASSA_TOKEN = "381764678:TEST:82679"

admins = ADMINS
storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)

# определение состояний используемых в боте
class Help(StatesGroup):
    waiting_message = State()

# создание основной клавиатуры
main_keyboard = InlineKeyboardMarkup()
button1 = InlineKeyboardButton('file1', callback_data='file1')  # кнопка для выбора файла
button_cnl = InlineKeyboardButton("Отмена", callback_data='cancel')
main_keyboard.add(button1)
main_keyboard.add(button_cnl)

# создание клавиатуры для помощи
keyboard_help = InlineKeyboardMarkup()
btn_help = InlineKeyboardButton('Помощь', callback_data='help')  # кнопка помощи
keyboard_help.add(btn_help, button_cnl)

# команды start и help
@dp.message_handler(commands=["start", "help"])
async def start_or_help(message: types.Message):
    if message.text == "/start":
        # отправка приветственного сообщения основной клавиатуры
        await message.answer(f'Здравствуйте {message.from_user.username}!')
        await message.answer('Для покупки выберите необходимый вариант ниже', reply_markup=main_keyboard)
    elif message.text == "/help":
        await message.answer("Выберите необходимое действие", reply_markup=keyboard_help)

# обработчик нажатия на кнопку "Помощь"
@dp.callback_query_handler(text='help')
async def cal_help(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()  # Ответим, чтобы убрать уведомление о загрузке
    await callback.message.answer("Тут будет текст помощи")

# обработчик нажатия на кнопку "file1"
@dp.callback_query_handler(text='file1')
async def payment(callback: types.CallbackQuery):
    await bot.send_invoice(chat_id=callback.from_user.id, title='Покупка', description='Покупка файла 1',
                           payload='payment', provider_token=UKASSA_TOKEN, currency='RUB', start_parameter='test_bot',
                           prices=[{'label': 'Руб', 'amount': 10000}])

# обработчик запроса предварительной проверки
@dp.pre_checkout_query_handler()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    # подтверждение оплаты
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# обработчик успешной оплаты
@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def process_pay(message: types.Message):
    if message.successful_payment.invoice_payload == 'payment':
        # подтверждение оплаты и отправка файла
        await bot.send_message(message.from_user.id, "Вы купили файл")
        await message.reply_document(open("01.txt", 'rb'))

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
