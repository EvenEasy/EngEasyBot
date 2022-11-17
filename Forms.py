import aiogram
from aiogram.dispatcher.filters.state import State, StatesGroup

class TestForms(StatesGroup):
    test = State()

class AdminForms(StatesGroup):
    change_test_limit = State()
    remove_question = State()

    enter_question = State()
    enter_level = State()
    enter_options = State()

    select_question = State()

    select_question_edit = State()
    select_what_edit = State()
    edit_question = State()
    edit_level = State()
    edit_options = State()