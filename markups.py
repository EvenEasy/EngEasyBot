import aiogram
from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup



Menu = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton("Телеграм канал", url="https://t.me/angli3i"),
        InlineKeyboardButton("Пройти тест", callback_data="start_test")
    ]
])

AdminPanel = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton("Почати гру", callback_data="game_start")],
        [InlineKeyboardButton("Створити гру", callback_data="create_game")],
        [InlineKeyboardButton("Список учасників", callback_data="game_participant")],
        [InlineKeyboardButton("Відправити повідомлення", callback_data="send_messages")]
    ]
)

game_level_markup = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton("Junior", callback_data="level_Junior")],
    [InlineKeyboardButton("Middle", callback_data="level_Middle")],
    [InlineKeyboardButton("Senior", callback_data="level_Senior")],
    [InlineKeyboardButton("All Levels", callback_data="level_All levels")]
])

def start_game_markup(game_code : str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Грати", callback_data=f"join_game_{game_code}")]
    ])

exit_game_markup = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton("Вийти", callback_data="exit_game")]
])

def support_markup(chat_id):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton("Відповісти", callback_data=f"answer_user_{chat_id}")]])

def reg_markups(game_code : int):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton("Зареєструватись", callback_data=f"reg_game_{game_code}")]])

def murkup_welcome(_dict : dict):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for key in list(_dict.keys()):
        markup.add(key)
    return markup