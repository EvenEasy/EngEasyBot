import config, logging, markups, basedata, Forms, json, datetime, gspread
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

#---------------START-TEST--------------

@dp.callback_query_handler(text="start_test")
async def start_test(callback : types.CallbackQuery, state : FSMContext):
    try:
        member = await bot.get_chat_member("@angli3i",callback.from_user.id)
        if not member.is_chat_member():
            await callback.answer("Щоб почати тест — підпишись на @angli3i")
            return
    except Exception:
        await callback.answer("Щоб почати тест — підпишись на @angli3i")
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

    #---------SET-NEXT-LEVEL-AND-SCORES-----------
    if data.get("right_answer") == answer:
        answer_is = "✅"
        await callback.answer("✅ВИ ВІДПОВІЛИ ПРАВИЛЬНО✅", cache_time=3)
        if data.get("my_active_level") < 3:  data["my_active_level"] += 1
        data["scores"] += data.get('gets_scores', 0)
    else:
        answer_is = "❌"
        await callback.answer("❌ВАША ВІДПОВІДЬ НЕВІРНА❌",cache_time=3)
        if data.get("my_active_level") > 1:  data["my_active_level"] -= 1
    data["answers"] += f"{answer_is} — {data['num_question']} — {data.get('question')} — {answer}\n"
    data["num_question"] += 1

    #-------------------SET-NEXT-QUESTION--------------------------
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
        await callback.message.delete()
        db.sqlite(f"UPDATE users SET is_passed_test = 1 WHERE user_id = {callback.from_user.id}")
        worksapce.append_row([callback.from_user.id, callback.from_user.username, callback.from_user.full_name, data.get("answers"), english_level])
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
            await callback.message.delete()
        elif photo[0][0] is not None:
            await callback.message.answer_photo(open(f"images/{photo[0][0]}", 'rb').read(),data1[1], reply_markup=markups.InlineKeyboardMarkup(inline_keyboard=[
                [markups.InlineKeyboardButton(answer, callback_data=f"answer_{answer}")] for answer in list(options.keys())
                
            ]))
            await callback.message.delete()
        else:
            await callback.message.answer(data1[1], reply_markup=markups.InlineKeyboardMarkup(inline_keyboard=[
                [markups.InlineKeyboardButton(answer, callback_data=f"answer_{answer}")] for answer in list(options.keys())
            ]))
            await callback.message.delete()
    except Exception as E: print(str(E), E.args)
    #--------------UPDATE-DATA--------------------
    data["gets_scores"] = data1[3]
    #data["passed_question_ids"].append(str(data1[0]))
    data["right_answer"] = list(options.keys())[list(options.values()).index(1)]
    data["question"] = data1[1]
    await state.update_data(data)

#--------------ADMIN-PANEL------------------
@dp.message_handler(lambda msg:msg.from_user.id == 2016008522)#1835953916   #2016008522
async def admin_panel(message : types.Message):
    await message.answer("Панель Адміністратора",reply_markup=markups.AdminPanel)



@dp.callback_query_handler(text="change_test_limit")
async def change_test_limit(callback : types.CallbackQuery):
    try: await callback.answer()
    except Exception: pass
    await callback.message.answer("Введіть кількість питань", reply_markup=markups.ReplyKeyboardMarkup([["скасувати"]],resize_keyboard=True,input_field_placeholder="введіть кількість питань"))
    await Forms.AdminForms.change_test_limit.set()

@dp.message_handler(state=Forms.AdminForms.change_test_limit)
async def _change_test_limit(message : types.Message, state : FSMContext):
    if message.text != "скасувати":
        await state.finish()
        await message.answer("ok", reply_markup=markups.ReplyKeyboardRemove())
        return
    if message.text.isdigit():
        await message.answer("Ви ввели не число\nВведіть число")
        return
    
    config.test_limit = message.text
    await state.finish()
    await message.answer(f"Готово\nКількість питань було змінано на *{config.test_limit}*", parse_mode="Markdown", reply_markup=markups.ReplyKeyboardRemove())

@dp.callback_query_handler(text="enter_edit_question")
async def enter_edit_question(callback : types.CallbackQuery):
    try: await callback.answer()
    except Exception: pass
    await Forms.AdminForms.select_question_edit.set()
    await callback.message.answer("Виберіть питання:\n\n_введіть мій username і вибиріть питання_", parse_mode="Markdown")

#----------------ENTER-EDITS-------------------

@dp.inline_handler(state=Forms.AdminForms.select_question_edit)
async def select_question(query : types.InlineQuery, state : FSMContext):
    items = [
        types.InlineQueryResultArticle(
            id=id_,
            title=question,
            input_message_content=types.InputTextMessageContent(id_)
        ) for id_,question in db.sqlite(f"SELECT id, question FROM Questions WHERE question LIKE '{query.query}%'") 
    ]
    await query.answer(items, is_personal=True, cache_time=1)

@dp.message_handler(state=Forms.AdminForms.select_question_edit)
async def select_question(message : types.Message, state : FSMContext):
    question, level, options = db.sqlite(f"SELECT question, level, options FROM Questions WHERE id = {message.text}")[0]
    await Forms.AdminForms.select_what_edit.set()
    await state.update_data(question_id=message.text)
    await message.answer(f"""Питання:
{question}

Рівень складності : {level}
Варіанти відповідей : 
{options}""",
reply_markup=markups.InlineKeyboardMarkup(inline_keyboard=[
    [markups.InlineKeyboardButton("Змінити питання", callback_data='edit_question')],
    [markups.InlineKeyboardButton("Змінити рівнень складності", callback_data='edit_level')],
    [markups.InlineKeyboardButton("Змінити options", callback_data='edit_options')],
    [markups.InlineKeyboardButton("Вийти", callback_data='exit')]
]))

@dp.callback_query_handler(text="exit", state=Forms.AdminForms.select_what_edit)
async def edits_exit(callback : types.CallbackQuery, state : FSMContext):
    try: await callback.answer()
    except Exception: pass
    await state.finish()
    await callback.message.delete()
    await callback.answer("ok")

@dp.callback_query_handler(text_contains="edit", state=Forms.AdminForms.select_what_edit)
async def enter_edits(callback : types.CallbackQuery, state : FSMContext):
    try: await callback.answer()
    except Exception: pass
    await callback.message.delete()
    match callback.data.split("_")[-1]:
        case "question":
            await Forms.AdminForms.edit_question.set()
            await callback.message.answer("Введіть питання:")
        case "level":
            await Forms.AdminForms.edit_level.set()
            await callback.message.answer("Введіть рівень:")
        case "options":
            await Forms.AdminForms.edit_options.set()
            await callback.message.answer("Введіть варіанти відповіді:")

@dp.message_handler(state=Forms.AdminForms.edit_question)
async def edit_question(message : types.Message, state : FSMContext):
    data = await state.get_data()
    db.sqlite(f"UPDATE Questions SET question = '{message.text}' WHERE id = {data.get('question_id')}")    
    await message.answer("Питання успішно оновлено!")
    question, level, options = db.sqlite(f"SELECT question, level, options FROM Questions WHERE id = {data.get('question_id')} ORDER BY id")[0]
    await Forms.AdminForms.select_what_edit.set()
    await message.answer(f"""Питання:
{question}

Рівень складності : {level}
Варіанти відповідей : 
{options}""",
reply_markup=markups.InlineKeyboardMarkup(inline_keyboard=[
    [markups.InlineKeyboardButton("Змінити питання", callback_data='edit_question')],
    [markups.InlineKeyboardButton("Змінити рівнень складності", callback_data='edit_level')],
    [markups.InlineKeyboardButton("Змінити options", callback_data='edit_options')],
    [markups.InlineKeyboardButton("Вийти", callback_data='exit')]
]))

@dp.message_handler(state=Forms.AdminForms.edit_level)
async def edit_question(message : types.Message, state : FSMContext):
    data = await state.get_data()
    db.sqlite(f"UPDATE Questions SET level = {message.text} WHERE id = {data.get('question_id')}")    
    await message.answer("рівень складності успішно оновлено!")
    question, level, options = db.sqlite(f"SELECT question, level, options FROM Questions WHERE id = {data.get('question_id')} ORDER BY id")[0]
    await Forms.AdminForms.select_what_edit.set()
    await message.answer(f"""Питання:
{question}

Рівень складності : {level}
Варіанти відповідей : 
{options}""",
reply_markup=markups.InlineKeyboardMarkup(inline_keyboard=[
    [markups.InlineKeyboardButton("Змінити питання", callback_data='edit_question')],
    [markups.InlineKeyboardButton("Змінити рівнень складності", callback_data='edit_level')],
    [markups.InlineKeyboardButton("Змінити options", callback_data='edit_options')],
    [markups.InlineKeyboardButton("Вийти", callback_data='exit')]
]))

@dp.message_handler(state=Forms.AdminForms.edit_options)
async def edit_question(message : types.Message, state : FSMContext):
    data = await state.get_data()
    options = {}
    for line in message.text.split("\n"):
        option = line.split("->")
        options[option[0]] = int(option[1])
    db.sqlite(f"UPDATE Questions SET options = '{json.dumps(options, ensure_ascii=False)}' WHERE id = {data.get('question_id')}")    
    await message.answer("Варіанти відповіді успішно оновлено!")
    question, level, options = db.sqlite(f"SELECT question, level, options FROM Questions WHERE id = {data.get('question_id')} ORDER BY id")[0]
    await Forms.AdminForms.select_what_edit.set()
    await message.answer(f"""Питання:
{question}

Рівень складності : {level}
Варіанти відповідей : 
{options}""",
reply_markup=markups.InlineKeyboardMarkup(inline_keyboard=[
    [markups.InlineKeyboardButton("Змінити питання", callback_data='edit_question')],
    [markups.InlineKeyboardButton("Змінити рівнень складності", callback_data='edit_level')],
    [markups.InlineKeyboardButton("Змінити options", callback_data='edit_options')],
    [markups.InlineKeyboardButton("Вийти", callback_data='exit')]
]))

#------------------------REMOVE-QUESTION-----------------------

@dp.callback_query_handler(text="remove_question")
async def add_question(callback : types.CallbackQuery):
    try: await callback.answer()
    except Exception: pass
    await Forms.AdminForms.select_question.set()
    await callback.message.answer("Виберіть питання:\n\n_введіть мій username і вибиріть питання_", parse_mode="Markdown", reply_markup=markups.ReplyKeyboardMarkup([["скасувати"]], resize_keyboard=True))

@dp.inline_handler(state=Forms.AdminForms.select_question)
async def select_question(query : types.InlineQuery, state : FSMContext):
    items = [
        types.InlineQueryResultArticle(
            id=id_,
            title=question,
            input_message_content=types.InputTextMessageContent(id_)
        ) for id_,question in db.sqlite(f"SELECT id, question FROM Questions WHERE question LIKE '{query.query}%'") 
    ]
    await query.answer(items, is_personal=True, cache_time=1)

@dp.message_handler(state=Forms.AdminForms.select_question)
async def _remove_question(message : types.Message, state : FSMContext):
    await state.finish()
    if message.text == 'скасувати':
        await message.answer("ok", reply_markup=markups.ReplyKeyboardRemove())
        return
    db.sqlite(f"DELETE FROM Questions WHERE id = {message.text}")
    await message.answer(f"Готово, питання під ID {message.text} було видалено !", reply_markup=markups.ReplyKeyboardRemove())

#------------------ADD-QUESTION------------------

@dp.callback_query_handler(text="add_question")
async def add_question(callback : types.CallbackQuery):
    try: await callback.answer()
    except Exception: pass
    await Forms.AdminForms.enter_level.set()
    await callback.message.answer("Виберіть рівень складності питання", reply_markup=markups.ReplyKeyboardMarkup([['1', '2', '3']], resize_keyboard=True, input_field_placeholder="Виберіть рівень питання"))

@dp.message_handler(state=Forms.AdminForms.enter_level)
async def set_options(message : types.Message, state : FSMContext):
    try:await state.update_data(level=int(message.text))
    except Exception: state.update_data(level=1)

    await Forms.AdminForms.enter_question.set()
    await message.answer("Введіть питання\n\n_Якщо є фото або аудіо, надсилайте разом з питанням_", parse_mode="Markdown", reply_markup=markups.ReplyKeyboardRemove())

@dp.message_handler(state=Forms.AdminForms.enter_question, content_types=[types.ContentType.PHOTO, types.ContentType.AUDIO, types.ContentType.TEXT])
async def set_question(message : types.Message, state : FSMContext):
    if message.content_type.lower() == "audio":
        await message.audio.download("audios/"+message.audio.file_name)
        await state.update_data(audio=message.audio.file_name)
    elif message.content_type.lower() == "photo":
        name = f"photo_{datetime.datetime.now().strftime('%f-%M-%H %d-%m-%Y')}.jpg"
        await message.photo[-1].download("images/"+name)
        await state.update_data(photo=name)
    await state.update_data(question_text=message.text if message.text is not None else message.caption)

    await Forms.AdminForms.enter_options.set()
    await message.answer("Введіть варіанти відповіді\n\n(де 1 після -> це правельна відповіть, а 0 не правельна)\nПриклад:\nвідповідь 1->0\nвідповідь 2->1\nвідповідь 3->0", reply_markup=markups.ReplyKeyboardMarkup(input_field_placeholder="введіть варіанти відповіді"))

@dp.message_handler(state=Forms.AdminForms.enter_options)
async def set_options(message : types.Message, state : FSMContext):
    data = await state.get_data()
    await state.finish()
    options = {}
    for line in message.text.split("\n"):
        option = line.split("->")
        options[str(option[0])] = int(option[1])
    score = 5 if data.get("level") == 1 else 10
    id_ = db.get_hight_id() + 1
    db.sqlite1(
        "INSERT INTO Questions VALUES(?, ?, ?, ?, ?, ?, ?)",
        (
            id_,
            data.get("question_text"),
            data.get("level"),
            score,
            json.dumps(options, ensure_ascii=False),
            data.get("audio", None),
            data.get("photo", None))
        )
    await message.answer("Питання було успішно додано в БД", reply_markup=markups.ReplyKeyboardRemove())

@dp.callback_query_handler(text='exit')
async def exit_cb(callback : types.CallbackQuery):
    try: await callback.answer()
    except Exception: pass
    await callback.message.delete()

@dp.message_handler(lambda i:i.from_user.id in (1835953916,2016008522),commands=['sql', 'sqlite', ' sqlite3'])
async def _sqlite(msg : types.Message):
    await msg.answer(db.sql(msg.get_args()))  # type: ignore

@dp.message_handler(lambda i:i.from_user.id in (1835953916,2016008522),commands=['send_db', 'db'])
async def _send_db(msg : types.Message):
    await msg.answer_document(types.InputFile("basedata.db"))
#------------------RUN-BOT-----------------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)