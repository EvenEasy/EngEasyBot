import aiogram
from aiogram.dispatcher.filters.state import State, StatesGroup

class TestForms(StatesGroup):
    test = State()

class AdminForms(StatesGroup):
    title_game = State()
    description_game = State()
    level_game = State()
    date_game = State()
    options = State()

    game_process = State()
    game_participant_process = State()
