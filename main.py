import config, logging, markups, basedata, Forms, json, datetime, gspread, random, asyncio, aiogram, os
from aiogram.dispatcher import FSMContext
from aiogram import Dispatcher, Bot, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from datetime import datetime

logging.basicConfig(level=logging.INFO)

bot = Bot(config.TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
db = basedata.BaseData("basedata.db")

gc = gspread.service_account(filename="credentials.json")
sh = gc.open_by_key(config.GOOGLESHEETSKEY)
worksapce = sh.sheet1
worksapce1 = sh.get_worksheet(1)
worksapce2 = sh.get_worksheet(2)

admins = (2016008522,1835953916)

@dp.message_handler(commands=['start'])
async def start(message : types.Message):
    user = db.sqlite(f'SELECT * FROM users WHERE user_id = {message.from_user.id}')
    if user == []:
        try: print("User - {0.username}[{0.id}] started use the bot at {1}".format(message.from_user, datetime.now().strftime('%H:%M:%S:%f %d/%m/%Y')))
        except Exception: pass
        db.sqlite(f"INSERT INTO users (user_id, full_name, is_passed_test) VALUES ({message.from_user.id}, '{message.from_user.full_name}', 0)")
    await message.answer_voice(types.InputFile("audios/Вітання.mp3"),
        f"""Вітаю, *{message.from_user.first_name}*!""",parse_mode="Markdown",reply_markup=markups.murkup_welcome(config.welcome_pages.get("1")[1]))

    cell = worksapce2.find(str(message.from_user.id), in_column=1)
    member = await bot.get_chat_member("@angli3i", message.from_user.id)
    isSub = 'Так' if member.is_chat_member() else 'Ні'
    if cell is None:
        worksapce2.append_row([
            datetime.now().strftime('%d.%m.%Y - %H:%M'),
            None,
            'Junior',
            message.from_user.full_name,
            message.from_user.username,
            None,
            0,
            'Так',
            isSub,
            message.from_user.id
        ])
    

@dp.my_chat_member_handler(lambda i:i.new_chat_member.status == "kicked")
async def user_block(UpdateData : types.ChatMemberUpdated):
    cell = worksapce2.find(str(UpdateData.from_user.id), in_column=1)
    if cell is not None:
        worksapce2.update_acell(f"Н{cell.row}",'Ні')

@dp.my_chat_member_handler()
async def user_block(UpdateData : types.ChatMemberUpdated):
    cell = worksapce2.find(str(UpdateData.from_user.id), in_column=1)
    if cell is not None:
        worksapce2.update_acell(f"Н{cell.row}",'Так')

@dp.callback_query_handler(text="welcome_page_reg")
async def reg_welcome_page(callback : types.CallbackQuery):
    try: await callback.answer()
    except Exception: pass
    game = db.get_new_game(None)
    print(game)
    if game:
        date_to_start = (datetime.strptime(game[4],"%d.%m.%Y %H:%M")-datetime.now()).total_seconds()
        date_to_start = f"{int(date_to_start // 3600)} години" if date_to_start >= 3600 else f"{int(date_to_start // 60)} хв."
        num_played_games = db.sqlite(f"SELECT num_played_games FROM Users WHERE user_id = '{callback.from_user.id}'")
        num_played_games = num_played_games[0][0] if num_played_games is not None and num_played_games[0][0] != 0 else 1
        price = num_played_games if num_played_games < 1 else 49
        prices = [
        types.LabeledPrice(label="Реєстрація на гру", amount=price*100)
        ]
        try: await bot.send_invoice(
            callback.from_user.id,
            title=game[0],
            description=game[1],
            provider_token=config.PAYMENTPROVIDERTOKEN,
            currency="UAH",
            prices=prices,
            start_parameter=f"reg_game_{game[3]}",
            payload=f"reg_game_{game[3]}"
        )
        except aiogram.utils.exceptions.ChatNotFound: pass
        await callback.message.answer(f"*{game[0]}*\n\n{game[1]}\n\nпочаток через *{date_to_start}*", reply_markup=markups.reg_markups(game[3]), parse_mode='Markdown')
    else:
        await callback.message.answer("На даний момент активних ігр немає")

@dp.callback_query_handler(text_contains="welcome_page_")
async def welcome_page(callback : types.CallbackQuery):
    page = callback.data.split('_')[-1]
    try: await callback.answer()
    except Exception: pass
    data = config.welcome_pages.get(page)
    if data[0] is not None:await callback.message.answer_voice(types.InputFile(f"audios/{data[0]}"), reply_markup=markups.murkup_welcome(data[1]))
    else: await callback.message.answer("Меню", reply_markup=markups.murkup_welcome(data[1]))
    cell = worksapce2.find(str(callback.from_user.id), in_column=1)
    if cell is not None:
        worksapce2.update_acell(f"F{cell.row}", f"{page} {data[0][:-4:] if data[0] is not None else 'Меню'}")

#=============================GAME=============================

@dp.callback_query_handler(text_contains="reg_game_")
async def reg_game(callback : types.CallbackQuery):
    print(callback.data)
    game_code = callback.data.split('_')[-1]
    if db.sqlite1("SELECT user_id FROM GameUsers WHERE user_id = ? AND game_code = ?", (callback.from_user.id, game_code)):
        await callback.answer("Ви вже зареєстровані на гру", True)
        return
    try: await callback.answer()
    except Exception: pass
    db.reg_player(callback.from_user.id, callback.from_user.username, game_code)
    await callback.message.answer("Ви були успішно зареєстровані")
    game = db.sqlite(f"SELECT * FROM Games WHERE game_code = '{game_code}' AND is_started = 0")
    print(game_code, game)
    if not game:
        await callback.message.answer("Гра не знайдена")
        return
    game = game[0]
    prices = [
        types.LabeledPrice(label="Реєстрація на гру", amount=100)
    ]
    try: await bot.send_invoice(
        callback.from_user.id,
        title=game[0],
        description=game[1],
        provider_token=config.PAYMENTPROVIDERTOKEN,
        currency="EUR",
        prices=prices,
        start_parameter=f"reg_game_{game[3]}",
        payload=f"reg_game_{game[3]}"
    )
    except aiogram.utils.exceptions.ChatNotFound: pass

@dp.message_handler(lambda i:i.from_user.id in admins,commands=['admin'])
async def admin_panel(message : types.Message):
    await message.answer(f"""АДМІН ПАНЕЛЬ""",reply_markup=markups.AdminPanel)

#============================SUPPORT===========================

@dp.message_handler(lambda i: not i.is_command() and i.from_user.id not in admins)
async def support_messages_handler(message : types.Message):
    await bot.send_message(2016008522,"""КОРИСТУВАЧ : {0.from_user.full_name} [ {0.from_user.username} ]

Повідомлення:
{0.text}""".format(message), reply_markup=markups.support_markup(message.from_id))

@dp.callback_query_handler(text_contains="answer_user_")
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

@dp.message_handler(state=Forms.AdminForms.answer_support)
async def answer_user_message(message : types.Message, state : FSMContext):
    if message.text == "Скасувати":
        await state.finish()
        await message.answer("Відповідь скасована", reply_markup=types.ReplyKeyboardRemove())
        return
    data = await state.get_data()
    await state.finish()
    await data.get('callback_message').delete_reply_markup()
    try:await bot.send_message(data.get('chat_id', None), message.text)
    except Exception: pass
    
    await message.answer("Повідомлення було відправлено !", reply_markup=types.ReplyKeyboardRemove())

#============================PLAYERS LIST============================

@dp.callback_query_handler(text="game_participant")
async def game_list(callback : types.CallbackQuery):
    try: await callback.answer()
    except Exception: pass
    markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(title, callback_data=f"player_list_{game_code}")] for title, game_code in db.sqlite("SELECT DISTINCT title, game_code FROM GAMES")
    ])
    markup.inline_keyboard.append([types.InlineKeyboardButton("Повернутися до меню", callback_data="back_to_admin_panel")])
    await callback.message.answer("Виберіть гру", reply_markup=markup)

@dp.callback_query_handler(text_contains="player_list_")
async def get_game_lost(callback : types.CallbackQuery):
    try: await callback.answer()
    except Exception: pass

    game_code = callback.data.split('_')[-1]
    players = "Username [ Score ] \n"
    for username, scores in db.sqlite(f"SELECT Username, Score FROM GameUsers WHERE game_code = '{game_code}'"):
        players+=f"{username} [ {scores} ]\n"

    await callback.message.answer(players)
    await callback.message.answer(f"""АДМІН ПАНЕЛЬ""",reply_markup=markups.AdminPanel)
    

#=========================CREATE GAME==========================

@dp.callback_query_handler(text="create_game")
async def get_participant(callback : types.CallbackQuery):
    try: await callback.answer()
    except Exception: pass
    await callback.message.answer("Введіть назву гри", reply_markup=types.ReplyKeyboardMarkup([["Скаcувати"]],True,input_field_placeholder="введіть назву гри"))
    await Forms.AdminForms.title_game.set()

@dp.message_handler(state=Forms.AdminForms.title_game)
async def get_participant(message : types.Message, state : FSMContext):
    if message.text == "Скаcувати":
        await state.finish()
        await message.answer("Створені гри скачовано", reply_markup=types.ReplyKeyboardRemove())
        await message.answer(f"""АДМІН ПАНЕЛЬ""",reply_markup=markups.AdminPanel)
        return
    await message.answer("Введіть опис гри", reply_markup=types.ReplyKeyboardMarkup([["Скаcувати"]],True,input_field_placeholder="введіть опис гри"))
    await state.update_data(title=message.text)
    await Forms.AdminForms.description_game.set()

@dp.message_handler(state=Forms.AdminForms.description_game)
async def get_participant(message : types.Message, state : FSMContext):
    if message.text == "Скаcувати":
        await state.finish()
        await message.answer("Створені гри скачовано", reply_markup=types.ReplyKeyboardRemove())
        await message.answer(f"""АДМІН ПАНЕЛЬ""",reply_markup=markups.AdminPanel)
        return
    await message.answer("Введіть дату\nDD.MM.YY HH:MM", reply_markup=types.ReplyKeyboardMarkup([["Скаcувати"]],True,input_field_placeholder="DD.MM.YY HH:MM"))
    await state.update_data(description=message.text)
    await Forms.AdminForms.date_game.set()

@dp.message_handler(state=Forms.AdminForms.date_game)
async def get_participant(message : types.Message, state : FSMContext):
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
    
@dp.callback_query_handler(state=Forms.AdminForms.level_game, text_contains="level")
async def get_participant(callback : types.CallbackQuery, state : FSMContext):
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
    db.sqlite1(
        f"INSERT INTO Games VALUES (?,?,?,?,?, 0)",
        (
            data.get("title", None), 
            data.get("description", None),
            data.get("level", None),
            CODE2FA,
            data.get("date_time", None)
        ))
    await Forms.AdminForms.options.set()

@dp.message_handler(content_types=[types.ContentType.TEXT, types.ContentType.PHOTO, types.ContentType.AUDIO],state=Forms.AdminForms.options)
async def get_participant(message : types.Message, state : FSMContext):
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

#=========================START GAME============================

@dp.callback_query_handler(text="game_start")
async def start_game(callback : types.CallbackQuery):
    try: await callback.answer()
    except Exception: pass
    ls = [[types.InlineKeyboardButton(title, callback_data=f"start_game_{code}")] for title, code in db.sqlite("SELECT title, game_code FROM Games WHERE is_started = 0")]
    ls.append([types.InlineKeyboardButton("Повернутися до меню", callback_data="back_to_admin_panel")])
    await callback.message.edit_text("АДМІН ПАНЕЛЬ\nВиберіть гру",reply_markup=types.InlineKeyboardMarkup(
        inline_keyboard=ls
    ))

@dp.callback_query_handler(text_contains="start_game_")
async def start_game(callback : types.CallbackQuery, state : FSMContext):
    game_code = callback.data.split('_')[-1]
    db.sqlite1("UPDATE Games SET is_started = 1 WHERE game_code = ?",(game_code,))
    await Forms.GameForms.game_process.set()
    for user_id in db.get_list_users(game_code):
        try: 
            await bot.send_message(
                int(user_id),
                "Гра розпочалася, для того щоб зіграти, натисніть *Грати*",
                parse_mode='Markdown',
                reply_markup=markups.start_game_markup(game_code)
            )
        except Exception: pass
    await callback.message.answer(
        "Гра почалася\nЩоб запустити 1 питання натисніть *Наступне питання*",
        parse_mode='Markdown',
        reply_markup=types.ReplyKeyboardMarkup(
            [
                ["Наступне питання","Завершити гру"],
                ["Рейтинг", "Відправити повідомлення усім гравцям"]
            ],
            True
        )
    )
    await state.update_data(
        game_code=game_code,
        answers=""
    )

@dp.callback_query_handler(text_contains="join_game", state='*')
async def start_game_user(callback : types.CallbackQuery, state : FSMContext):
    try: await callback.answer()
    except Exception: pass
    await Forms.GameForms.game_participant_process.set()
    game_code = callback.data.split('_')[-1]
    config.list_active_players.append(callback.from_user.id)
    await callback.message.answer("Очікуйте перше питання", reply_markup=types.ReplyKeyboardMarkup([['Дізнатись позицію']], True))
    await callback.message.delete_reply_markup()
    await state.update_data(
        answers='',
        game_code=game_code
        )

@dp.callback_query_handler(state=Forms.GameForms.game_participant_process,text="exit_game")
async def exit_game(callback : types.CallbackQuery, state : FSMContext):
    try: await callback.answer()
    except Exception: pass
    data = await state.get_data()
    await state.finish()
    await callback.message.answer("Ви вийшли з гри", reply_markup=types.ReplyKeyboardRemove())
    await callback.message.delete_reply_markup()
    try: title = db.sqlite(f"SELECT title FROM Games WHERE game_code = '{data.get('game_code')}'")[0]
    except IndexError: title = None
    db.sqlite(f"UPDATE Users SET num_played_games = num_played_games + 1 WHERE user_id = {callback.from_user.id}")
    worksapce1.append_row([
        callback.from_user.id,
        callback.from_user.username,
        data.get("answers"),
        title,
        db.sqlite(f"SELECT Score FROM GameUsers WHERE user_id = {callback.from_user.id}")[0],
        db.sqlite(f"SELECT level FROM Users WHERE user_id = {callback.from_user.id}")[0],
    ])

@dp.message_handler(text="Наступне питання", state=Forms.GameForms.game_process)
async def questions(message : types.Message, state : FSMContext):
    data = await state.get_data()
    question = db.get_game_question(data.get("_round", 1), data.get("game_code", None))
    if question is None:
        await message.answer("Питання закінчилися")
        return
    await message.answer(question[0])
    markup = types.InlineKeyboardMarkup()
    i=1
    for answer,value in json.loads(question[3]).items():
        markup.add(types.InlineKeyboardButton(answer, callback_data=f"answer{i}_{data.get('_round', 1)}_{value}"))
        i+=1
    if question[1] is None:
        for user_id in config.list_active_players:
            config.question_messages.append(await bot.send_message(int(user_id), question[0], reply_markup=markup))
    else:
        match question[1].split('.')[-1]:
            case 'png':
                for user_id in config.list_active_players:
                    config.question_messages.append(await bot.send_photo(int(user_id), types.InputFile(question[1]), question[0], reply_markup=markup))
            case 'mp3':
                for user_id in config.list_active_players:
                    config.question_messages.append(await bot.send_voice(int(user_id), types.InputFile(question[1]), question[0], reply_markup=markup))

    await message.answer("Питання було розіслане всім гравцям")
    await state.update_data(_round=data.get("_round", 1)+1)
    ls = config.question_messages

    await asyncio.sleep(30)
    for message in ls:
        try: await message.delete_reply_markup()
        except Exception: pass

@dp.message_handler(text="Завершити гру", state=Forms.GameForms.game_process)
async def finish_game(message : types.Message, state : FSMContext):
    await message.answer("Гра завершина !", reply_markup=types.ReplyKeyboardRemove())
    data = await state.get_data()
    await state.finish()
    game_winner = db.game_winner(data.get("game_code", None))
    db.sqlite(f"DELETE FROM Games WHERE game_code = '{data.get('game_code')}'")
    db.sqlite(f"DELETE FROM GamesComponents WHERE game_code = '{data.get('game_code')}'")
    
    for user_id in config.list_active_players:
        await bot.send_message(int(user_id), f"Гра завершина !\nПереможець : {game_winner[0]} | {game_winner[1]} балів \n\nНатисніть *вийти* щоб вийти з гри", parse_mode='Markdown', reply_markup=markups.exit_game_markup)
    await message.answer(f"""АДМІН ПАНЕЛЬ""",reply_markup=markups.AdminPanel)
    config.list_active_players = []

@dp.message_handler(text="Відправити повідомлення усім гравцям", state=Forms.GameForms.game_process)
async def send_message(callback : types.CallbackQuery, state : FSMContext):
    await callback.message.answer("Введіть повідомлення", reply_markup=types.ReplyKeyboardMarkup([["Скаcувати"]],True))
    await Forms.GameForms.send_message.set()

@dp.message_handler(state=Forms.GameForms.send_message)
async def message(message : types.Message, state : FSMContext):
    await Forms.GameForms.game_process.set()
    if message.text=="Скаcувати":
        await message.answer("Відправка скасована!", reply_markup=types.ReplyKeyboardMarkup(
            [
                ["Наступне питання","Завершити гру"],
                ["Рейтинг", "Відправити повідомлення усім гравцям"]
            ],
            True
        ))
        return
    for user_id in config.list_active_players:
        await bot.send_message(user_id, message.text)
    await message.answer("Повідомлення було відправленно усім гравцям !", reply_markup=types.ReplyKeyboardMarkup(
            [
                ["Наступне питання","Завершити гру"],
                ["Рейтинг", "Відправити повідомлення усім гравцям"]
            ],
            True
        ))
    

@dp.message_handler(lambda i:i.text == "Дізнатись позицію",state='*')#Forms.GameForms.game_participant_process)
async def game_game_pos(message : types.Message, state : FSMContext):
    data = await state.get_data()
    board = ""
    higest_scores = db.get_higest_scores(data.get('game_code'))
    higest_scores_ls = list(higest_scores.keys())
    isnotleaders = False
    limiter = dict(zip(higest_scores_ls, [0,0,0]))

    for i, info in enumerate(db.sqlite(f"SELECT Username, Score, user_id FROM GameUsers WHERE game_code = '{data.get('game_code')}' ORDER BY Score DESC"), 1):
        if (str(info[1]) in higest_scores_ls and limiter.get(str(info[1]), 1) < 3) or info[2] == message.from_user.id:
            try:limiter[str(info[1])]+=1
            except Exception: pass
            board+=f"{higest_scores.get(str(info[1]), i)} ( {info[1]} ) — @{info[0]}\n"
        if not isnotleaders and info[2] == message.from_user.id:
            isnotleaders = True
        if not isnotleaders and str(info[1]) not in higest_scores_ls:
            isnotleaders = True
            board += '\n...\n\n'

    await message.answer(board)

@dp.message_handler(lambda i:i.text == "Рейтинг",state=Forms.GameForms.game_process)
async def game_game_pos(message : types.Message, state : FSMContext):
    data = await state.get_data()
    board = ""
    higest_scores = db.get_higest_scores(data.get('game_code'))
    for i, info in enumerate(db.sqlite(f"SELECT Username, Score FROM GameUsers WHERE game_code = '{data.get('game_code')}' ORDER BY Score DESC"),1):
        board+=f"{higest_scores.get(str(info[1]), i)} ( {info[1]} ) — @{info[0]}\n"
    with open("board.txt", 'w', encoding='utf-8') as file:
        file.write(board)
    try:await message.answer_document(types.InputFile('board.txt'))
    except aiogram.utils.exceptions.BadRequest: await message.answer("Рейтинг пустий")

@dp.callback_query_handler(state=Forms.GameForms.game_participant_process,text_contains="answer")
async def game_answer(callback : types.CallbackQuery, state : FSMContext):
    await callback.message.delete_reply_markup()
    data = await state.get_data()
    if callback.data.split('_')[-1] == "1":
        data["answers"] += f"{{data.get('_round', 0)}} - {callback.message.text if callback.message.text is not None else callback.message.caption} - ✅\n"
        db.update_score(1, callback.from_user.id, data.get('game_code'))
        await bot.send_message(2016008522, f"Користувач {callback.from_user.id}\nВідповів : Правильно")
        await callback.answer("✅",show_alert=True)
    else:
        data["answers"] += f"{data.get('_round', 0)} - {callback.message.text if callback.message.text is not None else callback.message.caption} - ❌\n"
        await bot.send_message(2016008522, f"Користувач {callback.from_user.id}\nВідповів : Не правильно")
        await callback.answer("❌",show_alert=True)
    await state.update_data(data)

@dp.pre_checkout_query_handler()
async def checkout_process(pre_checkout_query : types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    print(pre_checkout_query.as_json())
    db.reg_player(pre_checkout_query.from_user.id, pre_checkout_query.from_user.username, pre_checkout_query.invoice_payload.split('_')[-1])

@dp.message_handler(content_types=[types.ContentType.SUCCESSFUL_PAYMENT])
async def successful_payment(message : types.Message):
    print(message.text)
    game_code = message.text.split('_')[-1]
    print(game_code)
    db.reg_player(message.from_user.id, message.from_user.username, game_code)

@dp.callback_query_handler(text="back_to_admin_panel")
async def back_to_admin_panel(callback : types.CallbackQuery):
    await callback.message.edit_text("АДМІН ПАНЕЛЬ",reply_markup=markups.AdminPanel)

@dp.message_handler(content_types=types.ContentTypes.SUCCESSFUL_PAYMENT)
async def Successful_Payment(message : types.Message):
    await message.answer("текст")

#==========================NOTIFICATE==========================

async def on_startup(dispecher : Dispatcher):
    loop = asyncio.get_event_loop()
    now = datetime.now()
    for _date, game_code in db.datetime_list:
        difference = (_date-now).total_seconds()
        if difference > 7200: loop.call_later(difference-7200, notify_call, game_code, "2 години")
        if difference > 300 : loop.call_later(difference-300, notify_call, game_code, "5 хв")

async def notify(game_code : str, message : str):
    ls = db.get_list_users(game_code)
    for user_id in ls:
        try: await bot.send_message(user_id, f"Гра почнеться через {message}")
        except aiogram.utils.exceptions.ChatNotFound: pass

def notify_call(game_code : str, message : str):
    tasks = set()
    task = asyncio.create_task(notify(game_code,message))
    tasks.add(task)
    task.add_done_callback(tasks.discard)

#=========================SEND MESSAGES========================

@dp.callback_query_handler(text="send_messages")
async def send_messages(callback : types.CallbackQuery):
    await Forms.AdminForms.select_receiver.set()
    await callback.answer("Виберіть приймача повідомлення")
    await callback.message.answer("Виберіть приймача повідомлення:\n\nвведіть мій Username та виберіть людину")

@dp.inline_handler(state=Forms.AdminForms.select_receiver)
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

@dp.message_handler(state=Forms.AdminForms.select_receiver)
async def chosen_inline(message : types.Message, state : FSMContext):
    await state.update_data(receiver=message.text)
    await Forms.AdminForms.send_message.set()
    await message.answer(f"Введіть повідомлення:", reply_markup=types.ReplyKeyboardMarkup([["Скасувати"]],True,True, input_field_placeholder="введіть повідомлення"))

@dp.message_handler(state=Forms.AdminForms.send_message, content_types=[
    types.ContentType.ANY
])
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




#======================BASEDATA COMMANDS=======================

@dp.message_handler(lambda i:i.from_user.id in (1835953916,2016008522),commands=['sql', 'sqlite', ' sqlite3'])
async def _sqlite(msg : types.Message):
    await msg.answer(db.sqlite(msg.get_args()))  # type: ignore

@dp.message_handler(lambda i:i.from_user.id in (1835953916,2016008522),commands=['send_db', 'db'])
async def _send_db(msg : types.Message):
    await msg.answer_document(types.InputFile("basedata.db"))

#===========================RUN BOT============================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)