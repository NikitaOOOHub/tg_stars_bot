from aiogram import Router, types
from aiogram.filters import Command
from aiogram.enums import ChatMemberStatus

router = Router()

# Временная заглушка для функции форматирования текста
def format_text_with_user_data(text: str, user: types.User) -> str:
    if not text:
        return ""
    username = f"@{user.username}" if user.username else "пользователь"
    return text.replace('{ID}', str(user.id)).replace('{@username}', username).replace('{full_name}', user.full_name)

# Временная заглушка для главного меню
async def show_main_menu(message: types.Message, repo, config, user):
    await message.answer("Главное меню (временно)")

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("✅ Бот работает! Команда /start получена.")
