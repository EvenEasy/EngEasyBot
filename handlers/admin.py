import markups, Forms, os, json
from aiogram import types, Dispatcher
from create_bot import dp, db, bot
from aiogram.dispatcher import FSMContext

admins = (2016008522,1835953916)


async def admin_panel(message : types.Message):
    await message.answer(f"""АДМІН ПАНЕЛЬ""",reply_markup=markups.AdminPanel)

async def back_to_admin_panel(callback : types.CallbackQuery):
    await callback.message.edit_text("АДМІН ПАНЕЛЬ",reply_markup=markups.AdminPanel)


async def send_message(callback : types.CallbackQuery):
    await Forms.AdminForms.select_receiver.set()
    await callback.answer("Виберіть приймача повідомлення")
    await callback.message.answer("Виберіть приймача повідомлення:\n\nвведіть мій Username та виберіть людину")

async def inline_query(query : types.InlineQuery, state : FSMContext):
    item = [
        types.InlineQueryResultArticle(
            id=user_id,
            title=username,
            input_message_content=types.InputTextMessageContent(user_id),
            description=level
        ) for user_id, username, level in db.get_receivers_list(query.query)
    ]
    await query.answer(item, is_personal=True, cache_time=1)

async def chosen_inline(message : types.Message, state : FSMContext):
    await state.update_data(receiver=message.text)
    await Forms.AdminForms.send_message.set()
    await message.answer(f"Введіть повідомлення:", reply_markup=types.ReplyKeyboardMarkup([["Скасувати"]],True,True, input_field_placeholder="введіть повідомлення"))

async def send_messages(message : types.Message, state : FSMContext):
    if message.content_type == types.ContentType.TEXT and message.text == "Скасувати":
        await state.finish()
        await message.answer(f"""АДМІН ПАНЕЛЬ""",reply_markup=markups.AdminPanel)
        return
    await message.answer("Повідомлення було відправлено !", reply_markup=types.ReplyKeyboardRemove())
    data = await state.get_data()
    await state.finish()
    match message.content_type:
        case types.ContentType.TEXT:
            for user_id, in db.get_receiver(data.get('receiver')):
                await bot.send_message(user_id, message.text)
        case types.ContentType.PHOTO:
            await message.photo[-1].download(f'temp/photo_{message.from_user.id}.jpg')
            inputFile = types.InputFile(f'temp/photo_{message.from_user.id}.jpg')
            for user_id, in db.get_receiver(data.get('receiver')):
                await bot.send_photo(user_id, inputFile,message.caption)
            os.remove(f'temp/photo_{message.from_user.id}.jpg')
        case types.ContentType.VOICE:
            await message.voice.download(f'temp/voice_{message.from_user.id}.mp3')
            inputFile = types.InputFile(f'temp/voice_{message.from_user.id}.mp3')
            for user_id, in db.get_receiver(data.get('receiver')):
                await bot.send_voice(user_id, inputFile,message.caption)
            os.remove(f'temp/voice_{message.from_user.id}.mp3')
        case types.ContentType.VIDEO_NOTE:
            await message.video_note.download(f'temp/video_note_{message.from_user.id}.mp4')
            inputFile = types.InputFile(f'temp/video_note_{message.from_user.id}.mp4')
            for user_id, in db.get_receiver(data.get('receiver')):
                await bot.send_video_note(user_id, inputFile,message.caption)
            os.remove(f'temp/video_note_{message.from_user.id}.mp4')


async def game_list(callback : types.CallbackQuery):
    try: await callback.answer()
    except Exception: pass
    markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(title, callback_data=f"player_list_{game_code}")] for title, game_code in db.sqlite("SELECT DISTINCT title, game_code FROM GAMES")
    ])
    markup.inline_keyboard.append([types.InlineKeyboardButton("Повернутися до меню", callback_data="back_to_admin_panel")])
    await callback.message.answer("Виберіть гру", reply_markup=markup)

async def get_game_list(callback : types.CallbackQuery):
    try: await callback.answer()
    except Exception: pass

    game_code = callback.data.split('_')[-1]
    players = "Username [ Score ] \n"
    for username, scores in db.sqlite(f"SELECT Username, Score FROM GameUsers WHERE game_code = '{game_code}'"):
        players+=f"{username} [ {scores} ]\n"

    await callback.message.answer(players)
    await callback.message.answer(f"""АДМІН ПАНЕЛЬ""",reply_markup=markups.AdminPanel)


async def edit_game(callback : types.CallbackQuery):
    ls = [[types.InlineKeyboardButton(title, callback_data=f"edit_game_{code}")] for title, code in db.sqlite("SELECT title, game_code FROM Games WHERE is_started = 0")]
    ls.append([types.InlineKeyboardButton("Повернутися до меню", callback_data="back_to_admin_panel")])
    await callback.message.edit_text("АДМІН ПАНЕЛЬ\nВиберіть гру",reply_markup=types.InlineKeyboardMarkup(
        inline_keyboard=ls
    ))
    await Forms.AdminForms.select_edit_game.set()

async def actions_game(callback : types.CallbackQuery, state : FSMContext):
    game_code = callback.data.split('_')[-1]
    game, = db.get_game(game_code, 'title')
    await state.update_data(game_code=game_code)
    await callback.message.edit_text(f"Гра {game}\n\nВиберіть питання:")
    await Forms.AdminForms.select_question.set()

async def inline_questions(query : types.InlineQuery, state : FSMContext):
    data = await state.get_data()
    item = [
        types.InlineQueryResultArticle(
            id=i,
            title=info[0],
            input_message_content=types.InputTextMessageContent(info[0]),
            description=info[1]
        ) for i,info in enumerate(db.get_questions(data.get('game_code'),query.query))
    ]
    await query.answer(item, is_personal=True, cache_time=1)

async def selected_question(message : types.Message, state : FSMContext):
    data = await state.get_data()
    await state.update_data(question=message.text)
    game = db.get_game(data.get("game_code"), 'title')
    await message.answer(f"Гра {game[0]}\n\nВиберіть питання:", reply_markup=markups.actinos)
    await Forms.AdminForms.select_action.set()

async def action_edit_question(callback : types.CallbackQuery, state : FSMContext):
    await callback.message.answer(f"введіть питання та варіанти відповідей гри\n\nПриклад:\nПитання\n\nвідповіть1:1\nвідповіть2:0\nвідповіть3:0\n")
    await Forms.AdminForms.edit_question.set()

async def edit_question(message : types.Message, state : FSMContext):
    data=await state.get_data()
    file_path = None
    options = None
    match message.content_type:
        case types.ContentType.PHOTO:
            if message.caption:
                text = message.caption.split("\n\n")
                question = text[0]
                try: options = text[1]
                except IndexError:
                    await message.answer("Не правильно ввели варіанти")
                    return
                await message.photo[-1].download(f"game files/{message.photo[-1].file_id}.png")
                file_path = f"game files/{message.photo[-1].file_id}.png"
        case types.ContentType.AUDIO:
            if message.caption:
                text = message.caption.split("\n\n")
                question = text[0]
                try: options = text[1]
                except IndexError:
                    await message.answer("Не правильно ввели варіанти")
                    return
            await message.audio.download(f"game files/{message.audio.file_name}.mp3")
            file_path = f"game files/{message.audio.file_name}.mp3"
        case _:
            if message.text:
                text = message.text.split("\n\n")
                question = text[0]
                try: options = text[1]
                except IndexError:
                    await message.answer("Не правильно ввели варіанти")
                    return
    if options:
        json_optinos = {}
        for option in options.split('\n'):
            option1 = option.split(':')
            json_optinos[option1[0]] = option1[-1].strip()
    db.sqlite1("UPDATE GamesComponents SET question = ?, file_path = ?, options = ? WHERE question = ?", (question, file_path, json.dumps(json_optinos, ensure_ascii=False), data.get("question")))
    await message.answer("Питання було зменено !", reply_markup=markups.actinos)
    await state.update_data(question=question)
    await Forms.AdminForms.select_action.set()

async def delete_game(callback : types.CallbackQuery, state : FSMContext):
    data = await state.get_data()
    db.sqlite(f"DELETE FROM GamesComponents WHERE question = '{data.get('question')}' AND game_code = '{data.get('game_code')}'")
    await state.finish()
    await callback.message.answer(f"""АДМІН ПАНЕЛЬ""",reply_markup=markups.AdminPanel)
async def exit_edit_game(callback : types.CallbackQuery, state : FSMContext):
    await callback.message.delete_reply_markup()
    await state.finish()
    await callback.message.answer(f"""АДМІН ПАНЕЛЬ""",reply_markup=markups.AdminPanel)

async def _sqlite(msg : types.Message):
    await msg.answer(db.sqlite(msg.get_args()))  # type: ignore

async def _send_db(msg : types.Message):
    await msg.answer_document(types.InputFile("basedata.db"))


#                REGISTER HANDLERS             #

def register_admin_handlers(dp : Dispatcher):
    dp.register_message_handler(admin_panel, lambda i:i.from_user.id in admins, commands=['admin'])
    dp.register_callback_query_handler(back_to_admin_panel, text="back_to_admin_panel")

    dp.register_callback_query_handler(send_message, text="send_messages")
    dp.register_inline_handler(inline_query, state=Forms.AdminForms.select_receiver)
    dp.register_message_handler(chosen_inline, state=Forms.AdminForms.select_receiver)
    dp.register_message_handler(send_messages, state=Forms.AdminForms.send_message, content_types=[types.ContentType.ANY])

    dp.register_callback_query_handler(edit_game)
    dp.register_callback_query_handler(actions_game, state=Forms.AdminForms.select_edit_game, text_contains="edit_game_")
    dp.register_inline_handler(inline_questions, state=Forms.AdminForms.select_question)
    dp.register_message_handler(selected_question, state=Forms.AdminForms.select_question)

    dp.register_callback_query_handler(action_edit_question, state=Forms.AdminForms.select_action, text="edit")
    dp.register_callback_query_handler(delete_game, state=Forms.AdminForms.select_action, text="delete")
    dp.register_callback_query_handler(exit_edit_game, state=Forms.AdminForms.select_action, text="exit_edit_game")

    dp.register_message_handler(edit_question, state=Forms.AdminForms.edit_question)

    dp.register_callback_query_handler(game_list, text="game_participant")
    dp.register_callback_query_handler(get_game_list, text_contains="player_list_")

    dp.register_message_handler(_sqlite, lambda i:i.from_user.id in admins,commands=['sql', 'sqlite', ' sqlite3'])
    dp.register_message_handler(_send_db, lambda i:i.from_user.id in admins,commands=['send_db', 'db'])
