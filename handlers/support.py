import markups, Forms, os, config
from aiogram import types, Dispatcher
from create_bot import dp, db, bot, user_workspace
from aiogram.dispatcher import FSMContext
from datetime import datetime

admins = (2016008522,1835953916)

async def support_messages_handler(message : types.Message):
    print("support handler")
    await bot.send_message(admins[1],"""КОРИСТУВАЧ : {0.from_user.full_name} [ {0.from_user.username} ]

Повідомлення:
{0.text}""".format(message), reply_markup=markups.support_markup(message.from_id))
    cell = user_workspace.find(str(message.from_user.id), in_column=10)
    if cell:
        user_workspace.update_acell(f'B{cell.row}', datetime.now().strftime('%d.%m.%Y - %H:%M'))

async def answer_user(callback : types.CallbackQuery, state : FSMContext):
    chat_id = callback.data.split('_')[-1]
    try: await callback.answer()
    except Exception: pass
    await Forms.AdminForms.answer_support.set()
    await state.update_data(
        chat_id=int(chat_id),
        callback_message=callback.message
    )
    await callback.message.answer(
        f"{callback.message.text}\n\nВведіть повідомлення:",
        reply_markup=types.ReplyKeyboardMarkup([["Скасувати"]], True, input_field_placeholder="введіть повідомлення для цього користувача")
    )

async def answer_user_message(message : types.Message, state : FSMContext):
    if message.text == "Скасувати":
        await state.finish()
        await message.answer("Відповідь скасована", reply_markup=types.ReplyKeyboardRemove())
        return
    data = await state.get_data()
    await state.finish()
    await data.get('callback_message').delete_reply_markup()
    print(data)
    match message.content_type:
        case types.ContentType.TEXT:
            for user_id, in db.get_receiver(data.get('chat_id')):
                await bot.send_message(user_id, message.text)
        case types.ContentType.PHOTO:
            await message.photo[-1].download(f'temp/photo_{message.from_user.id}.jpg')
            for user_id, in db.get_receiver(data.get('chat_id')):
                await bot.send_photo(user_id, types.InputFile(f'temp/photo_{message.from_user.id}.jpg'),message.caption)
            os.remove(f'temp/photo_{message.from_user.id}.jpg')
        case types.ContentType.VOICE:
            await message.voice.download(f'temp/voice_{message.from_user.id}.mp3')
            for user_id, in db.get_receiver(data.get('chat_id')):
                await bot.send_voice(user_id, types.InputFile(f'temp/voice_{message.from_user.id}.mp3'),message.caption)
            os.remove(f'temp/voice_{message.from_user.id}.mp3')
        case types.ContentType.VIDEO_NOTE:
            await message.video_note.download(f'temp/video_note_{message.from_user.id}.mp4')
            for user_id, in db.get_receiver(data.get('chat_id')):
                await bot.send_video_note(user_id, types.InputFile(f'temp/video_note_{message.from_user.id}.mp4'),message.caption)
            os.remove(f'temp/video_note_{message.from_user.id}.mp4')
    await message.answer("Повідомлення було відправлено !", reply_markup=types.ReplyKeyboardRemove())

def register_support_handlers(dp : Dispatcher):
    dp.register_message_handler(support_messages_handler, lambda i: i.text not in config.bttns_list and i.from_user.id not in admins)
    dp.register_callback_query_handler(answer_user, text_contains="answer_user_")
    dp.register_message_handler(answer_user_message, state=Forms.AdminForms.answer_support,  content_types=[types.ContentType.ANY])