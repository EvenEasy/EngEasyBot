import markups, config
from datetime import datetime
from aiogram import types, Dispatcher
from create_bot import dp, bot, db, user_workspace
from aiogram.utils.exceptions import ChatNotFound



async def start(message : types.Message):
    user = db.sqlite(f'SELECT * FROM users WHERE user_id = {message.from_user.id}')
    if user == []:
        try: print("User - {0.username}[{0.id}] started use the bot at {1}".format(message.from_user, datetime.now().strftime('%H:%M:%S:%f %d/%m/%Y')))
        except Exception: pass
        db.sqlite(f"INSERT INTO users (user_id, full_name, is_passed_test) VALUES ({message.from_user.id}, '{message.from_user.full_name}', 0)")
    await message.answer_sticker(types.InputFile('stickers/angli3i.tgs'))
    await message.answer_voice(types.InputFile(f"audios/{config.welcome_pages.get('1')[0]}"),
        f"""Вітаю, *{message.from_user.first_name}*!""",parse_mode="Markdown",reply_markup=markups.murkup_welcome(config.welcome_pages.get("1")[1]))

    cell = user_workspace.find(str(message.from_user.id), in_column=10)
    try:
        member = await bot.get_chat_member("@angli3i", message.from_user.id)
        isSub = 'Так' if member.is_chat_member() else 'Ні'
    except Exception: isSub = 'Невідомо'
    if cell is None:
        user_workspace.append_row([
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
    
async def reg_welcome_page(message : types.Message):
    level = db.get_user_info(message.from_user.id, 'level')[0]
    game = db.get_new_game(level)
    if game:
        date_to_start = (datetime.strptime(game[4],"%d.%m.%Y %H:%M")-datetime.now()).total_seconds()
        date_to_start = f"{int(date_to_start // 3600)} години" if date_to_start >= 3600 else f"{int(date_to_start // 60)} хв."
        num_played_games, = db.get_user_info(message.from_user.id, "num_played_games")
        price = 1 if num_played_games < 1 else 49
        prices = [
        types.LabeledPrice(label="Реєстрація на гру", amount=price*100)
        ]
        try:
            await bot.send_invoice(
                message.from_user.id,
                title=game[0],
                description=game[1],
                provider_token=config.PAYMENTPROVIDERTOKEN,
                currency="UAH",
                prices=prices,
                start_parameter=f"reg_game_{game[3]}",
                payload=f"reg_game_{game[3]}"
            )
        except Exception as E:
            print(str(E))
            await message.answer("Сталася якась помилка з платіжною системою")
    else:
        await message.answer("На даний момент активних ігр немає")

async def welcome_page(message : types.Message):
    data = config.welcome_pages.get(message.text)
    if data[0] is not None:await message.answer_voice(types.InputFile(f"audios/{data[0]}"), reply_markup=markups.murkup_welcome(data[1]))
    else: await message.answer("Меню", reply_markup=markups.murkup_welcome(data[1]))
    cell = user_workspace.find(str(message.from_user.id), in_column=10)
    if cell is not None:
        user_workspace.update_acell(f"F{cell.row}", message.text)

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
    except ChatNotFound: pass

#                MY CHAT MEMBER                #

async def user_block(UpdateData : types.ChatMemberUpdated):
    cell = user_workspace.find(str(UpdateData.from_user.id), in_column=10)
    if cell is not None:
        user_workspace.update_acell(f"Н{cell.row}",'Ні')

async def user_start(UpdateData : types.ChatMemberUpdated):
    cell = user_workspace.find(str(UpdateData.from_user.id), in_column=10)
    if cell is not None:
        user_workspace.update_acell(f"Н{cell.row}",'Так')

#                  PAYMENTS                    #

async def checkout_process(pre_checkout_query : types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    print(pre_checkout_query.as_json())
    db.reg_player(pre_checkout_query.from_user.id, pre_checkout_query.from_user.username, pre_checkout_query.invoice_payload.split('_')[-1])

async def successful_payment(message : types.Message):
    print(message.text)
    game_code = message.text.split('_')[-1]
    print(game_code)
    db.reg_player(message.from_user.id, message.from_user.username, game_code)


#                REGISTER HANDLERS             #

def register_user_handlers(dp : Dispatcher):
    dp.register_message_handler(start, commands=['start'])
    dp.register_message_handler(reg_welcome_page, text="ЗАРЕЄСТРУВАТИСЬ")
    dp.register_message_handler(welcome_page,lambda i:i.text in config.bttns_list)
    dp.register_callback_query_handler(reg_game, text_contains="reg_game_")

    dp.register_my_chat_member_handler(user_block,lambda i:i.new_chat_member.status == "kicked")
    dp.register_my_chat_member_handler(user_start)

    dp.register_pre_checkout_query_handler(checkout_process)
    dp.register_message_handler(successful_payment,content_types=[types.ContentType.SUCCESSFUL_PAYMENT])

