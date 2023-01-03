import Forms, markups, asyncio, json, config
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from create_bot import dp, bot, db, sh
from aiogram.utils.exceptions import BadRequest


async def start_game(callback : types.CallbackQuery):
    try: await callback.answer()
    except Exception: pass
    ls = [[types.InlineKeyboardButton(title, callback_data=f"start_game_{code}")] for title, code in db.sqlite("SELECT title, game_code FROM Games WHERE is_started = 0")]
    ls.append([types.InlineKeyboardButton("Повернутися до меню", callback_data="back_to_admin_panel")])
    await callback.message.edit_text("АДМІН ПАНЕЛЬ\nВиберіть гру",reply_markup=types.InlineKeyboardMarkup(
        inline_keyboard=ls
    ))

async def select_game(callback : types.CallbackQuery, state : FSMContext):
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

async def join_game(callback : types.CallbackQuery, state : FSMContext):
    try: await callback.answer()
    except Exception: pass
    await Forms.GameForms.game_participant_process.set()
    game_code = callback.data.split('_')[-1]
    index_worksheet = db.sqlite(f"SELECT worksheet_index FROM Games WHERE game_code = '{game_code}'")
    if not index_worksheet: index_worksheet = 2
    else: index_worksheet = index_worksheet[0][0]
    config.list_active_players.append(callback.from_user.id)
    await callback.message.answer("Очікуйте перше питання", reply_markup=types.ReplyKeyboardMarkup([['Дізнатись позицію']], True))
    await callback.message.delete_reply_markup()
    await state.update_data(
        answers='',
        game_code=game_code,
        index_worksheet=index_worksheet
        )

async def exit_game(callback : types.CallbackQuery, state : FSMContext):
    try: await callback.answer()
    except Exception: pass
    data = await state.get_data()
    await state.finish()
    await callback.message.answer("Ви вийшли з гри", reply_markup=types.ReplyKeyboardRemove())
    await callback.message.delete_reply_markup()
    db.sqlite(f"UPDATE Users SET num_played_games = num_played_games + 1 WHERE user_id = {callback.from_user.id}")
    game_worksapce = sh.get_worksheet(data.get('index_worksheet'))
    game_worksapce.append_row([
        0,
        callback.from_user.id,
        callback.from_user.username,
        data.get("answers"),
        db.sqlite(f"SELECT Score FROM GameUsers WHERE user_id = {callback.from_user.id}")[0]
    ])


async def next_question(message : types.Message, state : FSMContext):
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

async def finish_game(message : types.Message, state : FSMContext):
    await message.answer("Гра завершина !", reply_markup=types.ReplyKeyboardRemove())
    data = await state.get_data()
    await state.finish()
    game_winner = db.game_winner(data.get("game_code", None))
    workspace = sh.get_worksheet(db.get_game(data.get("game_code"), 'worksheet_index')[0])
    db.sqlite(f"DELETE FROM Games WHERE game_code = '{data.get('game_code')}'")
    db.sqlite(f"DELETE FROM GamesComponents WHERE game_code = '{data.get('game_code')}'")
    level = workspace.find(str(game_winner[0]), in_column=10)
    if level:
        level1 = workspace.row_values(level.row)
        rank_level = config.levels_rank.get(level1[2])
        new_rank_level = config.rank_levels.get(str(rank_level+1)) if rank_level+1 <= 3 else config.rank_levels.get(str(rank_level))
        workspace.update_acell(f'C{level.row}', new_rank_level)
        db.sqlite(f"UPDATE Users SET level = '{new_rank_level}' WHERE user_id = {game_winner[0]}")
    else:
        level = ''
        new_rank_level = ''
    for user_id in config.list_active_players:
        await bot.send_message(int(user_id), f"""ВіТАЄМО ГРАВЦіВ, 
ЯКі ПЕРЕЙШЛИ НА РІВЕНЬ {new_rank_level}.

1 МіСЦЕ : @{level}
PROMOTION : """, parse_mode='Markdown', reply_markup=markups.exit_game_markup)
    await message.answer(f"""АДМІН ПАНЕЛЬ""",reply_markup=markups.AdminPanel)
    config.list_active_players = []

async def send_message(callback : types.CallbackQuery, state : FSMContext):
    await callback.message.answer("Введіть повідомлення", reply_markup=types.ReplyKeyboardMarkup([["Скаcувати"]],True))
    await Forms.GameForms.send_message.set()

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
    

async def get_game_pos(message : types.Message, state : FSMContext):
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

async def raiting_board(message : types.Message, state : FSMContext):
    data = await state.get_data()
    board = ""
    higest_scores = db.get_higest_scores(data.get('game_code'))
    for i, info in enumerate(db.sqlite(f"SELECT Username, Score FROM GameUsers WHERE game_code = '{data.get('game_code')}' ORDER BY Score DESC"),1):
        board+=f"{higest_scores.get(str(info[1]), i)} ( {info[1]} ) — @{info[0]}\n"
    with open("board.txt", 'w', encoding='utf-8') as file:
        file.write(board)
    try:await message.answer_document(types.InputFile('board.txt'))
    except BadRequest: await message.answer("Рейтинг пустий")

async def game_answer(callback : types.CallbackQuery, state : FSMContext):
    await callback.message.delete_reply_markup()
    data = await state.get_data()
    if callback.data.split('_')[-1] == "1":
        data["answers"] += f"{{data.get('_round', 0)}} - {callback.message.text if callback.message.text is not None else callback.message.caption} - ✅\n"
        db.update_score(1, callback.from_user.id, data.get('game_code'))
        await bot.send_message(2016008522, f"Користувач {callback.from_user.id}\nВідповів : Правильно")
        await callback.message.answer_sticker(types.InputFile("stickers\yes.tgs"))
    else:
        data["answers"] += f"{data.get('_round', 0)} - {callback.message.text if callback.message.text is not None else callback.message.caption} - ❌\n"
        await bot.send_message(2016008522, f"Користувач {callback.from_user.id}\nВідповів : Не правильно")
        await callback.answer("❌",show_alert=True)
        await callback.message.answer_sticker(types.InputFile("stickers\no.tgs"))
    await state.update_data(data)

#                REGISTER HANDLERS             #

def register_game_process_handlers(dp : Dispatcher):
    dp.register_callback_query_handler(start_game, text="game_start")
    dp.register_callback_query_handler(select_game, text_contains="start_game_")
    dp.register_callback_query_handler(join_game, text_contains="join_game")
    dp.register_callback_query_handler(exit_game, state=Forms.GameForms.game_participant_process,text="exit_game")

    dp.register_message_handler(next_question, text="Наступне питання", state=Forms.GameForms.game_process)
    dp.register_message_handler(finish_game, text="Завершити гру", state=Forms.GameForms.game_process)
    dp.register_message_handler(send_message, text="Відправити повідомлення усім гравцям", state=Forms.GameForms.game_process)
    dp.register_message_handler(message, state=Forms.GameForms.send_message)

    dp.register_message_handler(get_game_pos,lambda i:i.text == "Дізнатись позицію",state=Forms.GameForms.game_participant_process)
    dp.register_message_handler(raiting_board, lambda i:i.text == "Рейтинг",state=Forms.GameForms.game_process)
    dp.register_callback_query_handler(game_answer, state=Forms.GameForms.game_participant_process,text_contains="answer")