import asyncio
import datetime
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import BoundFilter
from aiogram.utils.exceptions import BadRequest

from config import TOKEN

bot = Bot(token=TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)


class AdminFilter(BoundFilter):
    async def check(self, message: types.Message):
        member = await message.chat.get_member(message.from_user.id)
        return member.is_chat_admin()


class IsGroup(BoundFilter):
    async def check(self, message: types.Message):
        return message.chat.type in (
            types.ChatType.GROUP,
            types.ChatType.SUPERGROUP
        )


dp.filters_factory.bind(IsGroup)
dp.filters_factory.bind(AdminFilter)


async def set_default_commands(dp: Dispatcher):
    await dp.bot.set_my_commands([
        types.BotCommand('set_photo', 'установить фото в группе'),
        types.BotCommand('set_title', 'установить название'),
        types.BotCommand('ro', 'read only'),
        types.BotCommand('unro', 'read only off'),
    ])


@dp.message_handler(IsGroup(), commands='ban')
async def ban_user(message: types.Message):
    try:
        if not message.reply_to_message:
            await message.answer('fgh')
            return

        member = message.reply_to_message.from_user
        member_id = member.id
        chat_id = message.chat.id
        await message.chat.kick(user_id=member_id)
        await message.reply(f"пользователь {member.full_name} был забанен")

    except Exception:
        print('Ошибка')
        await message.reply(f"пользователь {member.full_name} был забанен")


@dp.message_handler(content_types=types.ContentType.NEW_CHAT_MEMBERS)
async def new_member(message: types.Message):
    await message.reply(f"Привет{message.new_chat_members[0].full_name}, в нашей группе запрещеные политичиские споры")


@dp.message_handler(content_types=types.ContentType.LEFT_CHAT_MEMBER)
async def ban_member(message: types.Message):
    await message.reply(f"Пользователь {message.left_chat_member.full_name}, покинул чат")


@dp.message_handler(IsGroup(), AdminFilter(), commands=['ro'])
async def read_only_mode(message: types.Message):
    if not message.reply_to_message:
        await message.answer('Используй reply')
        return

    member = message.reply_to_message.from_user
    chat_id = message.chat.id
    time = 1
    reason = 'spam'
    until_date = datetime.datetime.now() + datetime.timedelta(minutes=time)
    member_id = member.id
    ReadOnlyPermission = types.ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_polls=False,
        can_pin_messages=False,
        can_invite_users=True,
        can_change_info=False,
        can_add_web_page_previews=False
    )

    try:
        await bot.restrict_chat_member(chat_id, user_id=member_id, permissions=ReadOnlyPermission, until_date=until_date)
        response_message = await message.answer(f'Полбзователю {member.get_mention(as_html=True)} запрещено писать сообщения в течении {time} минут'
                                                f'По причине {reason}'
                                                f'Это сообщение будет удалено через 5 сек')

        await asyncio.sleep(10)
        await response_message.delete()

    except BadRequest as e:
        await message.answer(f'Не получилось замутить, по причине {str(e)}')


if __name__ == "__main__":
    # Запуск бота
    executor.start_polling(dp, skip_updates=True)
