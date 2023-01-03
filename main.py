from aiogram import executor
from create_bot import dp, on_startup

from handlers import admin, create_game, game_proces, user, support

#                REGISTER HANDLERS                #
admin.register_admin_handlers(dp)
user.register_user_handlers(dp)
support.register_support_handlers(dp)
create_game.register_game_create_handlers(dp)
game_proces.register_game_process_handlers(dp)



if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)