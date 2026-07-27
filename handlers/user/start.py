from aiogram import Router, types
from aiogram.filters import Command

router = Router()

# Временная заглушка для функции, которую импортируют другие файлы
async def show_main_menu(message: types.Message, repo, config, user):
    # Простой ответ, чтобы не падать
    await message.answer("Главное меню (временно)")

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("✅ Бот работает! Команда /start получена.")
