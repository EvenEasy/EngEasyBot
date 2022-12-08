import config, logging, markups, basedata, Forms, json, datetime, gspread, random
from aiogram.dispatcher import FSMContext
from aiogram import Dispatcher, Bot, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)

bot = Bot(config.TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
db = basedata.BaseData("basedata.db")

gc = gspread.service_account(filename="credentials.json")
sh = gc.open_by_key(config.GOOGLESHEETSKEY)
worksapce = sh.sheet1

admins = (2016008522,1835953916)

@dp.message_handler(commands=['start'])
async def start(message : types.Message):
    user = db.sqlite(f'SELECT * FROM users WHERE user_id = {message.from_user.id}')
    if user == []:
        try: print("User - {0.username}[{0.id}] started use the bot at {1}".format(message.from_user, datetime.datetime.now().strftime('%H:%M:%S:%f %d/%m/%Y')))
        except Exception: pass
        db.sqlite(f"INSERT INTO users VALUES ({message.from_user.id}, '{message.from_user.full_name}', 0)")
    await message.answer(
        f"""Вітаю, *{message.from_user.first_name}*!

Маєш неймовірну нагоду безкоштовно, швидко та максимально точно дізнатись рівень своєї англійської! Але, перед цим, з тебе підписка на наш телеграм канал 😈"""
    ,parse_mode="Markdown",reply_markup=markups.Menu)

#==========================START TEST==========================

@dp.callback_query_handler(text="start_test")
async def start_test(callback : types.CallbackQuery, state : FSMContext):
    try:
        member = await bot.get_chat_member("@angli3i",callback.from_user.id)
        if not member.is_chat_member():
            await callback.answer("Щоб почати тест — підпишись на @angli3i", True)
            return
    except Exception:
        await callback.answer("Щоб почати тест — підпишись на @angli3i", True)
        return
    try: await callback.answer()
    except Exception: pass
    
    if db.sqlite(f'SELECT * FROM users WHERE user_id = {callback.from_user.id}')[0][-1] == 1:
        await callback.message.answer("Ви вже здавали тест !")
        return
    try: print("User - {0.username}[{0.id}] started test at {1}".format(callback.from_user, datetime.datetime.now().strftime('%H:%M:%S:%f %d/%m/%Y')))
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
        try: print("User - {0.username}[{0.id}] ended test at {1}".format(callback.from_user, datetime.datetime.now().strftime('%H:%M:%S:%f %d/%m/%Y')))
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
        await callback.message.answer(f"*{game[0]}*\n\n{game[1]}\n\n{game[2]} | {game[4]}", parse_mode='Markdown')
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

@dp.message_handler(commands=['admin'])
async def admin_panel(message : types.Message):
    await message.answer(f"""АДМІН ПАНЕЛЬ""",reply_markup=markups.AdminPanel)


#=========================CREATE GAME==========================

@dp.callback_query_handler(text="create_game")
async def get_participant(callback : types.CallbackQuery):
    await callback.message.answer("Введіть назву гри", reply_markup=types.ReplyKeyboardMarkup([["Скаcувати"]],True,input_field_placeholder="введіть назву гри"))
    await Forms.AdminForms.title_game.set()

@dp.message_handler(state=Forms.AdminForms.title_game)
async def get_participant(message : types.Message, state : FSMContext):
    await message.answer("Введіть опис гри", reply_markup=types.ReplyKeyboardMarkup([["Скаcувати"]],True,input_field_placeholder="введіть опис гри"))
    await state.update_data(title=message.text)
    await Forms.AdminForms.description_game.set()

@dp.message_handler(state=Forms.AdminForms.description_game)
async def get_participant(message : types.Message, state : FSMContext):
    await message.answer("Введіть дату\nDD.MM.YY HH:MM", reply_markup=types.ReplyKeyboardMarkup([["Скаcувати"]],True,input_field_placeholder="DD.MM.YY HH:MM"))
    await state.update_data(description=message.text)
    await Forms.AdminForms.date_game.set()


@dp.message_handler(state=Forms.AdminForms.date_game)
async def get_participant(message : types.Message, state : FSMContext):
    await message.answer("Супер", reply_markup=markups.ReplyKeyboardRemove())
    await message.answer("Виберіть рівень гри", reply_markup=markups.game_level_markup)
    await state.update_data(date_time=message.text)
    await Forms.AdminForms.level_game.set()
    

@dp.callback_query_handler(state=Forms.AdminForms.level_game, text_contains="level")
async def get_participant(callback : types.CallbackQuery, state : FSMContext):
    await callback.message.answer(
        "введіть питання та варіанти відповідей гри",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                ["Завершити"]
            ],
            resize_keyboard=True,
            input_field_placeholder="введіть питання та варіанти відповідей гри"
        )
    )
    CODE2FA = random.choice(range(100000, 999999))
    await state.update_data({
        "level" : callback.data.split('_')[-1],
        "game code" : CODE2FA
    })
    data = await state.get_data()
    db.sqlite1(
        f"INSERT INTO Games VALUES (?,?,?,?,?)",
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
        print(data)
        await state.finish()
        await message.answer("Готово, гра була додана",reply_markup=markups.ReplyKeyboardRemove())
        return
    text = message.text.split("\n\n")
    question = text[0]
    options = text[1]
    db.sqlite1("INSERT INTO GamesComponents VALUES (?,?,?,?)", (question, None, data.get("game code"), options))

#=========================START GAME============================

@dp.callback_query_handler(text="game_start")
async def start_game(callback : types.CallbackQuery):
    ls = [[types.InlineKeyboardButton(title, callback_data=f"start_game_{code}")] for title, code in db.sqlite("SELECT title, game_code FROM Games WHERE is_started = 0")]
    ls.append([types.InlineKeyboardButton("Повернутися до меню", callback_data="back_to_admin_panel")])
    await callback.message.edit_text("АДМІН ПАНЕЛЬ\nВиберіть гру",reply_markup=types.InlineKeyboardMarkup(
        inline_keyboard=ls
    ))

@dp.callback_query_handler(text_contains="start_game_")
async def start_game(callback : types.CallbackQuery, state : FSMContext):
    game_code = callback.data.split('_')[-1]
    db.sqlite1("UPDATE Games SET is_started = 1 WHERE game_code = ?",(game_code,))
    await Forms.AdminForms.game_process.set()
    for user_id in config.list_active_players:
        await bot.send_message(int(user_id), "Гра розпочалася, для того щоб зіграти, натисніть *Грати*", reply_markup=markups.start_game_markup)
    await callback.message.answer(
        "Гра почалася\nЩоб запустити 1 питання натисніть *Наступне питання*",
        parse_mode='Markdown',
        reply_markup=types.ReplyKeyboardMarkup([["Наступне питання","Завершити гру"]],True)
    )
    await state.update_data(
        game_code=game_code,
        round=1,
        answers=""
    )

@dp.callback_query_handler(text="join_game")
async def start_game_user(callback : types.CallbackQuery):
    await Forms.AdminForms.game_participant_process.set()
    config.list_active_players.append(callback.from_user.id)
    await callback.answer("Очікуйте перший")
    await callback.message.delete_reply_markup()

@dp.callback_query_handler(text="exit_game")
async def exit_game(callback : types.CallbackQuery, state : FSMContext):
    await state.finish()
    await callback.answer("Ви вийшли з гри", cache_time=5)
    await callback.message.delete_reply_markup()

@dp.message_handler(text="Наступне питання", state=Forms.AdminForms.game_process)
async def questions(message : types.Message, state : FSMContext):
    data = await state.get_data()
    question = db.get_game_question(data.get("round", 1), data.get("game_code", None))
    await message.answer(question[0])
    markup = types.InlineKeyboardMarkup()
    i=1
    for answer,value in json.loads(question[3]).items():
        markup.add(types.InlineKeyboardButton(answer, callback_data=f"answer{i}_{data.get('round', 1)}_{value}"))
        i+=1
    for user_id in config.list_active_players:
        await bot.send_message(int(user_id), question[0], reply_markup=markup)
    await message.answer("Питання було розіслане всім гравцям")
    print(data)

@dp.message_handler(text="Завершити гру", state=Forms.AdminForms.game_process)
async def finish_game(message : types.Message, state : FSMContext):
    await message.answer("Гра завершина !")
    await state.finish()
    for user_id in config.list_active_players:
        await bot.send_message(int(user_id), "Гра завершина !\nНатисніть *вийти* щоб вийти з гри", reply_markup=markups.exit_game_markup)
    config.list_active_players = []

#Forms.AdminForms.game_participant_process
@dp.callback_query_handler(state="*",text_contains="answer")
async def game_answer(callback : types.CallbackQuery, state : FSMContext):
    await callback.message.delete_reply_markup()
    data = await state.get_data()
    if callback.data.split('_')[-1] == "1":
        data["answers"] += f"1 - ✅\n"
        await callback.answer("1 - ✅",show_alert=True)
    else:
        data["answers"] += f"1 - ❌\n"
        await callback.answer("1 - ❌",show_alert=True)
    await state.update_data(data)


'''@dp.message_handler(commands=['start'])
async def start_menu(message : types.Message):
    await message.answer(f"Hey *{message.from_user.id}* !\nMenu text", parse_mode='Markdown')
    prices = [
        types.LabeledPrice(label="Зеєстрація на гру", amount=10000)
    ]
    await bot.send_invoice(
        message.chat.id,
        title="Назва найблищої гри",
        description="Текст наблищої гри",
        provider_token=config.PAYMENTPROVIDERTOKEN,
        currency="uah",


    )'''


@dp.callback_query_handler(text="back_to_admin_panel")
async def back_to_admin_panel(callback : types.CallbackQuery):
    await callback.message.edit_text("АДМІН ПАНЕЛЬ",reply_markup=markups.AdminPanel)

@dp.message_handler(content_types=types.ContentTypes.SUCCESSFUL_PAYMENT)
async def Successful_Payment(message : types.Message):
    await message.answer("текст")

#======================BASEDATA COMMANDS=======================

@dp.message_handler(lambda i:i.from_user.id in (1835953916,2016008522),commands=['sql', 'sqlite', ' sqlite3'])
async def _sqlite(msg : types.Message):
    await msg.answer(db.sqlite(msg.get_args()))  # type: ignore

@dp.message_handler(lambda i:i.from_user.id in (1835953916,2016008522),commands=['send_db', 'db'])
async def _send_db(msg : types.Message):
    await msg.answer_document(types.InputFile("basedata.db"))
#===========================RUN BOT============================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)