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
        db.sqlite(f"UPDATE users SET is_passed_test = 1 WHERE user_id = {callback.from_user.id}")
        cell = worksapce.find(str(callback.from_user.id), in_column=1)
        worksapce.update_acell(f"D{cell.row}",data.get("answers"))
        worksapce.update_acell(f"E{cell.row}", english_level)
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

@dp.callback_query_handler(text='exit')
async def exit_cb(callback : types.CallbackQuery):
    try: await callback.answer()
    except Exception: pass
    await callback.message.delete()

@dp.message_handler(lambda i:i.from_user.id in (1835953916,2016008522),commands=['sql', 'sqlite', ' sqlite3'])
async def _sqlite(msg : types.Message):
    await msg.answer(db.sqlite(msg.get_args()))  # type: ignore

@dp.message_handler(lambda i:i.from_user.id in (1835953916,2016008522),commands=['send_db', 'db'])
async def _send_db(msg : types.Message):
    await msg.answer_document(types.InputFile("basedata.db"))
#------------------RUN-BOT-----------------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
