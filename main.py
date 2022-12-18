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

admins = (2016008522,1835953916)

@dp.message_handler(commands=['id'])
async def get_id(message : types.Message):
    await message.answer("User id `{0.id}`".format(message.from_user), parse_mode='Markdown')

@dp.message_handler(commands=['start'])
async def start(message : types.Message):
    user = db.sqlite(f'SELECT * FROM users WHERE user_id = {message.from_user.id}')
    if user == []:
        try: print("User - {0.username}[{0.id}] started use the bot at {1}".format(message.from_user, datetime.now().strftime('%H:%M:%S:%f %d/%m/%Y')))
        except Exception: pass
        db.sqlite(f"INSERT INTO users (user_id, full_name, is_passed_test) VALUES ({message.from_user.id}, '{message.from_user.full_name}', 0)")
    await message.answer(
        f"""Вітаю, *{message.from_user.first_name}*!

Маєш неймовірну нагоду безкоштовно, швидко та максимально точно дізнатись рівень своєї англійської! Але, перед цим, з тебе підписка на наш телеграм канал 😈"""
    ,parse_mode="Markdown",reply_markup=markups.Menu)

    level = db.sqlite(f"SELECT level FROM Users WHERE user_id = {message.from_user.id}")
    if level:
        game = db.get_new_game(level[0][0])
        date_to_start = (datetime.strptime(game[4],"%d.%m.%Y %H:%M")-datetime.now()).total_seconds()
        date_to_start = f"{int(date_to_start // 3600)} години" if date_to_start >= 3600 else f"{int(date_to_start // 60)} хв."
        await message.answer(f"*{game[0]}*\n\n{game[1]}\n\nпочаток через *{date_to_start}*", reply_markup=markups.reg_markups(game[3]), parse_mode='Markdown')

#==========================START TEST==========================

@dp.callback_query_handler(text="start_test")
async def start_test(callback : types.CallbackQuery, state : FSMContext):
    #comment 
    '''try:
        member = await bot.get_chat_member("@angli3i",callback.from_user.id)
        if not member.is_chat_member():
            await callback.answer("Щоб почати тест — підпишись на @angli3i", True)
            return
    except Exception:
        await callback.answer("Щоб почати тест — підпишись на @angli3i", True)
        return'''
    try: await callback.answer()
    except Exception: pass
    
    if db.sqlite(f'SELECT * FROM users WHERE user_id = {callback.from_user.id}')[0][-1] == 1:
        await callback.message.answer("Ви вже здавали тест !")
        return
    try: print("User - {0.username}[{0.id}] started test at {1}".format(callback.from_user, datetime.now().strftime('%H:%M:%S:%f %d/%m/%Y')))
    except Exception: pass
    data = db.get_question(2, 2)
    options = json.loads(data[4])
    photo = db.sqlite(f"SELECT photo FROM Questions WHERE id = {data[0]}")
    
    await Forms.TestForms.test.set()
    #--------------SEND-MESSAGE---------------------
    if data[5] is not None:
        await callback.message.answer_voice(open(f"audios/{data[5]}", 'rb').read(),data[1], reply_markup=markups.InlineKeyboardMarkup(inline_keyboard=[
            [markups.InlineKeyboardButton(answer, callback_data=f"answer_{answer}")] for answer in list(options.keys())
            
        ]))
    elif photo[0][0] is not None:
            await callback.message.answer_photo(open(f"images/{photo[0][0]}", 'rb').read(),data[1], reply_markup=markups.InlineKeyboardMarkup(inline_keyboard=[
            [markups.InlineKeyboardButton(answer, callback_data=f"answer_{answer}")] for answer in list(options.keys())
            
        ]))
    else:
        await callback.message.answer(data[1], reply_markup=markups.InlineKeyboardMarkup(inline_keyboard=[
            [markups.InlineKeyboardButton(answer, callback_data=f"answer_{answer}")] for answer in list(options.keys())
            
        ]))
    #--------------UPDATE-DATA--------------------
    await state.update_data({
        "right_answer": list(options.keys())[list(options.values()).index(1)],
        "question" : data[1],
        "gets_scores" : data[3],
        "num_question":1,
        "my_active_level" : 2,
        "scores" : 0,
        #"passed_question_ids" : [str(data[0])],
        "answers" : ""
    })

@dp.callback_query_handler(state=Forms.TestForms.test, text_contains="answer")
async def answer(callback : types.CallbackQuery, state : FSMContext):
    data = await state.get_data()
    answer = callback.data.split('_')[-1]
    try: await callback.message.delete_reply_markup()
    except Exception: pass

    #---------SET-NEXT-LEVEL-AND-SCORES-----------
    if data.get("right_answer") == answer:
        answer_is = "✅"
        if data.get("my_active_level") < 3:  data["my_active_level"] += 1
        await callback.message.answer_sticker(types.InputFile("stickers/AnimatedStickerYes.tgs"))
        data["scores"] += data.get('gets_scores', 0)
    else:
        answer_is = "❌"
        await callback.message.answer_sticker(types.InputFile("stickers/AnimatedStickerNo.tgs"))
        if data.get("my_active_level") > 1:  data["my_active_level"] -= 1
    data["answers"] += f"{answer_is} — {data['num_question']} — {data.get('question')} — {answer}\n"
    data["num_question"] += 1
#-----------------GAME-OUT-------------------------
    if data.get("num_question", 1) > config.test_limit:
        english_level = db.get_level(data["scores"])
        try: print("User - {0.username}[{0.id}] ended test at {1}".format(callback.from_user, datetime.now().strftime('%H:%M:%S:%f %d/%m/%Y')))
        except Exception: pass
        await callback.message.answer(f"""
Ви набрали {data["scores"]}%
Ваш рівень — *{english_level}*""", parse_mode="Markdown",reply_markup=markups.InlineKeyboardMarkup(inline_keyboard=[
    [markups.InlineKeyboardButton("Наш Tik Tok", url="https://www.tiktok.com/@angli3i?_t=8XLWY6lQNmf&_r=1")]
]))
        db.sqlite(f"UPDATE users SET is_passed_test = 1 WHERE user_id = {callback.from_user.id}")
        cell = worksapce.find(str(callback.from_user.id), in_column=1)
        if cell is not None:
            worksapce.update_acell(f"D{cell.row}", data.get("answers"))
            worksapce.update_acell(f"E{cell.row}", english_level)
        else:
            worksapce.append_row([callback.from_user.id, callback.from_user.username, callback.from_user.full_name, data.get("answers"), english_level])
        game = db.get_new_game(english_level)
        print(game)
        if game:
            date_to_start = (datetime.strptime(game[4],"%d.%m.%Y %H:%M")-datetime.now()).total_seconds()
            date_to_start = f"{int(date_to_start // 3600)} години" if date_to_start >= 3600 else f"{int(date_to_start // 60)} хв."
            await callback.message.answer(f"*{game[0]}*\n\n{game[1]}\n\nпочаток через *{date_to_start}*", reply_markup=markups.reg_markups(game[3]), parse_mode='Markdown')
        await state.finish()
        return

#--------------SEND-MESSAGE---------------------
    data1 = db.get_question(data.get("my_active_level"), data["num_question"])
    photo = db.sqlite(f"SELECT photo FROM Questions WHERE id = {data1[0]}")
    try: options = json.loads(data1[4])
    except Exception: options = None

    try:
        if data1[5] is not None:
            
            await callback.message.answer_voice(open(f"audios/{data1[5]}", 'rb').read(),data1[1], reply_markup=markups.InlineKeyboardMarkup(inline_keyboard=[
                [markups.InlineKeyboardButton(answer, callback_data=f"answer_{answer}")] for answer in list(options.keys())
            ]))
        elif photo[0][0] is not None:
            await callback.message.answer_photo(open(f"images/{photo[0][0]}", 'rb').read(),data1[1], reply_markup=markups.InlineKeyboardMarkup(inline_keyboard=[
                [markups.InlineKeyboardButton(answer, callback_data=f"answer_{answer}")] for answer in list(options.keys())
                
            ]))
        else:
            await callback.message.answer(data1[1], reply_markup=markups.InlineKeyboardMarkup(inline_keyboard=[
                [markups.InlineKeyboardButton(answer, callback_data=f"answer_{answer}")] for answer in list(options.keys())
            ]))
    except Exception as E: print(str(E), E.args)
    #--------------UPDATE-DATA--------------------
    data["gets_scores"] = data1[3]
    #data["passed_question_ids"].append(str(data1[0]))
    data["right_answer"] = list(options.keys())[list(options.values()).index(1)]
    data["question"] = data1[1]
    await state.update_data(data)

#=============================GAME=============================

@dp.callback_query_handler(text_contains="reg_game_")
async def reg_game(callback : types.CallbackQuery):
    game_code = callback.data.split('_')[-1]
    if db.sqlite1("SELECT user_id FROM GameUsers WHERE user_id = ? AND game_code = ?", (callback.from_user.id, game_code)):
        await callback.answer("Ви вже зареєстровані на гру", True)
        return
    try: await callback.answer()
    except Exception: pass
    game = db.sqlite(f"SELECT * FROM Games WHERE game_code = '{game_code}' AND is_started = 0")[0]
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

'''@dp.message_handler(lambda i: not i.is_command() and i.from_user.id not in admins)
async def support_messages_handler(message : types.Message):
    await bot.send_message(2016008522,"""КОРИСТУВАЧ : {0.from_user.full_name} [ {0.from_user.username} ]

Повідомлення:
{0.text}""".format(message), reply_markup=markups.support_markup(message.from_id))
'''
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
        return
    await message.answer("Введіть опис гри", reply_markup=types.ReplyKeyboardMarkup([["Скаcувати"]],True,input_field_placeholder="введіть опис гри"))
    await state.update_data(title=message.text)
    await Forms.AdminForms.description_game.set()

@dp.message_handler(state=Forms.AdminForms.description_game)
async def get_participant(message : types.Message, state : FSMContext):
    if message.text == "Скаcувати":
        await state.finish()
        await message.answer("Створені гри скачовано", reply_markup=types.ReplyKeyboardRemove())
        return
    await message.answer("Введіть дату\nDD.MM.YY HH:MM", reply_markup=types.ReplyKeyboardMarkup([["Скаcувати"]],True,input_field_placeholder="DD.MM.YY HH:MM"))
    await state.update_data(description=message.text)
    await Forms.AdminForms.date_game.set()

@dp.message_handler(state=Forms.AdminForms.date_game)
async def get_participant(message : types.Message, state : FSMContext):
    if message.text == "Скаcувати":
        await state.finish()
        await message.answer("Створені гри скачовано", reply_markup=types.ReplyKeyboardRemove())
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
        "game code" : CODE2FA
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
        for user_id, in db.sqlite(f"SELECT user_id FROM Users WHERE level {'NOT NULL' if level == 'All levels' else f'= {level}'}"):
            try: await bot.send_message(user_id,f"*{title}*\n\n{description}\n\nnпочаток через *{date_to_start}*", reply_markup=markups.reg_markups(game_code), parse_mode='Markdown')
            except Exception: pass
        # set notify 
        loop = asyncio.get_event_loop()
        difference = (datetime.strptime(data.get("date_time"),"%d.%m.%Y %H:%M")-datetime.now()).total_seconds()
        if difference > 7200: loop.call_later(difference-7200, notify_call, game_code, "2 години")
        if difference > 300 : loop.call_later(difference-300, notify_call, game_code, "5 хв")
        
        await message.answer("Готово, гра була додана",reply_markup=markups.ReplyKeyboardRemove())
        return

    file_path = None
    match message.content_type:
        case types.ContentType.PHOTO:
            text = message.caption.split("\n\n")
            question = text[0]
            options = text[1]
            await message.photo[-1].download(f"game files/{message.photo[-1].file_id}.png")
            file_path = f"game files/{message.photo[-1].file_id}.png"
        case types.ContentType.AUDIO:
            text = message.caption.split("\n\n")
            question = text[0]
            options = text[1]
            await message.audio.download(f"game files/{message.audio.file_name}")
            file_path = f"game files/{message.audio.file_name}.mp3"
        case _:
            text = message.text.split("\n\n")
            question = text[0]
            options = text[1]
    json_optinos = {}
    for option in options.split('\n'):
        json_optinos[option[:-2]] = option[-1:]
    db.sqlite1("INSERT INTO GamesComponents VALUES (?,?,?,?)", (question, file_path, data.get("game code"), json.dumps(json_optinos, ensure_ascii=False)))

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
        await bot.send_message(int(user_id), "Гра розпочалася, для того щоб зіграти, натисніть *Грати*",parse_mode='Markdown', reply_markup=markups.start_game_markup)
    await callback.message.answer(
        "Гра почалася\nЩоб запустити 1 питання натисніть *Наступне питання*",
        parse_mode='Markdown',
        reply_markup=types.ReplyKeyboardMarkup([["Наступне питання","Завершити гру"]],True)
    )
    await state.update_data(
        game_code=game_code,
        _round=1,
        answers=""
    )

@dp.callback_query_handler(text="join_game")
async def start_game_user(callback : types.CallbackQuery):
    await Forms.GameForms.game_participant_process.set()
    config.list_active_players.append(callback.from_user.id)
    await callback.answer("Очікуйте перше питання")
    await callback.message.delete_reply_markup()

@dp.callback_query_handler(state=Forms.GameForms.game_participant_process,text="exit_game")
async def exit_game(callback : types.CallbackQuery, state : FSMContext):
    data = await state.get_data()
    await state.finish()
    await callback.answer("Ви вийшли з гри", cache_time=5)
    await callback.message.delete_reply_markup()
    title = db.sqlite(f"SELECT title FROM Games WHERE game_code = '{data.get('game_code')}'")[0]
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
                file = types.InputFile(question[1])
                for user_id in config.list_active_players:
                    config.question_messages.append(await bot.send_photo(int(user_id), file, question[0], reply_markup=markup))
            case 'mp3':
                file = types.InputFile(question[1])
                for user_id in config.list_active_players:
                    config.question_messages.append(await bot.send_voice(int(user_id), file, question[0], reply_markup=markup))

    await message.answer("Питання було розіслане всім гравцям")
    await state.update_data(_round=data.get("_round")+1)
    ls = config.question_messages

    await asyncio.sleep(10)
    for message in ls:
        try: await message.delete_reply_markup()
        except Exception: pass

@dp.message_handler(text="Завершити гру", state=Forms.GameForms.game_process)
async def finish_game(message : types.Message, state : FSMContext):
    await message.answer("Гра завершина !", reply_markup=types.ReplyKeyboardRemove())
    data = await state.get_data()
    await state.finish()
    game_winner = db.game_winner(data.get("game_code", None))
    for user_id in config.list_active_players:
        await bot.send_message(int(user_id), f"Гра завершина !\nПереможець : {game_winner[0]} | {game_winner[1]} балів \n\nНатисніть *вийти* щоб вийти з гри", parse_mode='Markdown', reply_markup=markups.exit_game_markup)
    config.list_active_players = []
    config.question_messages = []

@dp.callback_query_handler(state=Forms.GameForms.game_participant_process,text_contains="answer")
async def game_answer(callback : types.CallbackQuery, state : FSMContext):
    await callback.message.delete_reply_markup()
    data = await state.get_data()
    if callback.data.split('_')[-1] == "1":
        data["answers"] += f"1 - ✅\n"
        db.update_score(1, callback.from_user.id, data.get('game_code'))
        await bot.send_message(admins[1], f"Користувач {callback.from_user.id}\nВідповів : Правильно")
        await callback.answer("1 - ✅",show_alert=True)
    else:
        data["answers"] += f"1 - ❌\n"
        await bot.send_message(admins[1], f"Користувач {callback.from_user.id}\nВідповів : Не правильно")
        await callback.answer("1 - ❌",show_alert=True)
    await state.update_data(data)

@dp.pre_checkout_query_handler()
async def checkout_process(pre_checkout_query : types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    print(pre_checkout_query.as_json())
    #db.reg_player(pre_checkout_query.from_user.id, pre_checkout_query.from_user.username, pre_checkout_query.invoice_payload.split('_')[-1])

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
    print("notify")
    ls = db.get_list_users(game_code)
    print(ls)
    for user_id in ls:
        try: await bot.send_message(user_id, f"Гра почнеться через {message}")
        except aiogram.utils.exceptions.ChatNotFound: pass

def notify_call(game_code : str, message : str):
    print("new task")
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