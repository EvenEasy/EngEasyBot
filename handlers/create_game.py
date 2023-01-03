import Forms, markups, random, asyncio, json
from datetime import datetime
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from create_bot import dp, bot, db, sh, notify_call




async def create_game(callback : types.CallbackQuery):
    try: await callback.answer()
    except Exception: pass
    await callback.message.answer("Введіть назву гри", reply_markup=types.ReplyKeyboardMarkup([["Скаcувати"]],True,input_field_placeholder="введіть назву гри"))
    await Forms.AdminForms.title_game.set()

async def set_title(message : types.Message, state : FSMContext):
    if message.text == "Скаcувати":
        await state.finish()
        await message.answer("Створені гри скачовано", reply_markup=types.ReplyKeyboardRemove())
        await message.answer(f"""АДМІН ПАНЕЛЬ""",reply_markup=markups.AdminPanel)
        return
    await message.answer("Введіть опис гри", reply_markup=types.ReplyKeyboardMarkup([["Скаcувати"]],True,input_field_placeholder="введіть опис гри"))
    await state.update_data(title=message.text)
    await Forms.AdminForms.description_game.set()

async def set_game_description(message : types.Message, state : FSMContext):
    if message.text == "Скаcувати":
        await state.finish()
        await message.answer("Створені гри скачовано", reply_markup=types.ReplyKeyboardRemove())
        await message.answer(f"""АДМІН ПАНЕЛЬ""",reply_markup=markups.AdminPanel)
        return
    await message.answer("Введіть дату\nDD.MM.YY HH:MM", reply_markup=types.ReplyKeyboardMarkup([["Скаcувати"]],True,input_field_placeholder="DD.MM.YY HH:MM"))
    await state.update_data(description=message.text)
    await Forms.AdminForms.date_game.set()

async def set_date_game(message : types.Message, state : FSMContext):
    if message.text == "Скаcувати":
        await state.finish()
        await message.answer("Створені гри скачовано", reply_markup=types.ReplyKeyboardRemove())
        await message.answer(f"""АДМІН ПАНЕЛЬ""",reply_markup=markups.AdminPanel)
        return
    try: datetime.strptime(message.text,"%d.%m.%Y %H:%M")
    except Exception: 
        await message.answer("Ви не вірно ввели дату, спробуйте ще раз")
        return
    await message.answer("Супер", reply_markup=markups.ReplyKeyboardRemove())
    await message.answer("Виберіть рівень гри", reply_markup=markups.game_level_markup)
    await state.update_data(date_time=message.text)
    await Forms.AdminForms.level_game.set()

async def set_level(callback : types.CallbackQuery, state : FSMContext):
    try: await callback.answer()
    except Exception: pass
    await callback.message.answer(
        "введіть питання та варіанти відповідей гри\n\nПриклад:\nПитання\n\nвідповіть1:1\nвідповіть2:0\nвідповіть3:0\n",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[["Завершити"]],
            resize_keyboard=True,
            input_field_placeholder="введіть питання та варіанти відповідей гри"
        )
    )
    while True:
        CODE2FA = random.choice(range(100000, 999999))
        if not db.sqlite(f"SELECT game_code FROM Games WHERE game_code = '{CODE2FA}'"): break
    await state.update_data({
        "level" : callback.data.split('_')[-1],
        "game_code" : CODE2FA
    })
    data = await state.get_data()
    new_game_worksheet = sh.add_worksheet(f"Гра {data.get('title')}", 1, 5)
    new_game_worksheet.append_row(["Місце", "user id","username","answers","Набрані бали за останю гру"])
    db.sqlite1(
        f"INSERT INTO Games VALUES (?,?,?,?,?, 0)",
        (
            data.get("title", None), 
            data.get("description", None),
            data.get("level", None),
            CODE2FA,
            data.get("date_time", None),
            new_game_worksheet.index
        ))
    await Forms.AdminForms.options.set()

async def enter_optinos(message : types.Message, state : FSMContext):
    data = await state.get_data()
    if message.text == "Завершити":
        await state.finish()
        title = data.get("title")
        description = data.get('description')
        game_code = data.get('game_code')
        level = data.get('level')
        # send notify new game for users

        date_to_start = (datetime.strptime(data.get('date_time'),"%d.%m.%Y %H:%M")-datetime.now()).total_seconds()
        date_to_start = f"{int(date_to_start // 3600)} години" if date_to_start >= 3600 else f"{int(date_to_start // 60)} хв."
        markup = markups.reg_markups(game_code)
        for user_id, in db.sqlite(f"""SELECT user_id FROM Users WHERE level {'NOT NULL' if level == 'All levels' else f"= '{level}'"}"""):
            try: await bot.send_message(user_id,f"*{title}*\n\n{description}\n\nпочаток через *{date_to_start}*", reply_markup=markup, parse_mode='Markdown')
            except Exception: pass
        # set notify 
        loop = asyncio.get_event_loop()
        difference = (datetime.strptime(data.get("date_time"),"%d.%m.%Y %H:%M")-datetime.now()).total_seconds()
        if difference > 7200: loop.call_later(difference-7200, notify_call, game_code, "2 години")
        if difference > 300 : loop.call_later(difference-300, notify_call, game_code, "5 хв")
        
        await message.answer("Готово, гра була додана",reply_markup=markups.ReplyKeyboardRemove())
        await message.answer(f"""АДМІН ПАНЕЛЬ""",reply_markup=markups.AdminPanel)
        return

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
    db.sqlite1("INSERT INTO GamesComponents VALUES (?,?,?,?)", (question, file_path, data.get("game_code"), json.dumps(json_optinos, ensure_ascii=False)))

#                REGISTER HANDLERS             #

def register_game_create_handlers(dp : Dispatcher):
    dp.register_callback_query_handler(create_game, text="create_game")
    dp.register_message_handler(set_title, state=Forms.AdminForms.title_game)
    dp.register_message_handler(set_game_description, state=Forms.AdminForms.description_game)
    dp.register_message_handler(set_date_game, state=Forms.AdminForms.date_game)
    dp.register_callback_query_handler(set_level, state=Forms.AdminForms.level_game, text_contains="level")
    dp.register_message_handler(enter_optinos, content_types=[types.ContentType.TEXT, types.ContentType.PHOTO, types.ContentType.AUDIO],state=Forms.AdminForms.options)