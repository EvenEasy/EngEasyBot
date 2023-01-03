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

    select_edit_game = State()
    select_question = State()
    select_action = State()
    edit_question = State()

    answer_support = State()
    
    select_receiver = State()
    send_message = State()

class GameForms(StatesGroup):
    game_process = State()
    game_participant_process = State()

    send_message = State()
