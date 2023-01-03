import config, gspread, asyncio
from datetime import datetime
from basedata import BaseData
from aiogram import Dispatcher, Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import ChatNotFound

bot = Bot(config.TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
db = BaseData("basedata.db")

gc = gspread.service_account(filename="credentials.json")
sh = gc.open_by_key(config.GOOGLESHEETSKEY)
user_workspace = sh.get_worksheet(1)
worksapce2 = sh.get_worksheet(2)

async def on_startup(dispecher : Dispatcher):
    print("Bot is connected")
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
        except ChatNotFound: pass

def notify_call(game_code : str, message : str):
    tasks = set()
    task = asyncio.create_task(notify(game_code,message))
    tasks.add(task)
    task.add_done_callback(tasks.discard)