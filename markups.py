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
        [
            InlineKeyboardButton("Почати гру", callback_data="game_start"),
            InlineKeyboardButton("Створити гру", callback_data="create_game"),
            InlineKeyboardButton("Список учасників", callback_data="game_participant")
        ]
    ]
)

game_level_markup = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton("BEGINNER (A1)", callback_data="level_BEGINNER (A1)")],
    [InlineKeyboardButton("PRE-INTERMEDIATE (A2)", callback_data="level_PRE-INTERMEDIATE (A2)")],
    [InlineKeyboardButton("INTERMEDIATE (B1)", callback_data="level_INTERMEDIATE (B1)")],
    [InlineKeyboardButton("UPPER-INTERMEDIATE (B2)", callback_data="level_UPPER-INTERMEDIATE (B2)")],
    [InlineKeyboardButton("ADVANCED (C1)", callback_data="level_ADVANCED (C1)")]
])

start_game_markup = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton("Грати", callback_data="join_game")]
])

exit_game_markup = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton("Вийти", callback_data="exit_game")]
])