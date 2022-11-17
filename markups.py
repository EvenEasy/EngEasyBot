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
        [InlineKeyboardButton("Додати питання", callback_data="add_question"), InlineKeyboardButton("Видалити питання", callback_data="remove_question")],
        [InlineKeyboardButton("Змінити кількість питань", callback_data="change_test_limit")],
        [InlineKeyboardButton("Внести зміни в питання", callback_data="enter_edit_question")]
    ]
)