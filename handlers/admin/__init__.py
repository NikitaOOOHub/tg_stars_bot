from aiogram import F, Router, types
from aiogram.filters import Command
from services.fragment_sender import FragmentSender
from . import panel, user_management, promos, price_control, settings, broadcast, fragment_status

router = Router()

# === Команда для ручной отправки звёзд ===
@router.message(Command("buy_for_user"))
async def cmd_buy_for_user(message: types.Message, fragment_sender: FragmentSender):
    args = message.text.split()
    if len(args) < 3:
        await message.answer(
            "❌ Формат: /buy_for_user <количество> <[id126570592|@username]>\n"
            "Пример: /buy_for_user 250 @username"
        )
        return

    try:
        amount = int(args[1])
        recipient = args[2].lstrip('@')
        if amount < 50 or amount > 1000000:
            await message.answer("❌ Количество должно быть от 50 до 1 000 000.")
            return
    except ValueError:
        await message.answer("❌ Количество должно быть числом.")
        return

    await message.answer(f"⏳ Покупаю {amount} звёзд для @{recipient}...")

    try:
        success = await fragment_sender.send_stars(recipient, amount)
        if success:
            await message.answer(f"✅ Успешно куплено {amount} звёзд для @{recipient}!")
        else:
            await message.answer(
                "❌ Ошибка при покупке. Возможные причины:\n"
                "- Недостаточно TON на кошельке\n"
                "- Истекли куки Fragment (обновите в .env)\n"
                "- Неверный юзернейм получателя\n"
                "Проверьте логи в консоли."
            )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# === Остальные админ-роутеры ===
def get_admin_router(admin_ids: list[int]) -> Router:
    admin_router = Router()
    admin_router.message.filter(F.from_user.id.in_(admin_ids))
    admin_router.callback_query.filter(F.from_user.id.in_(admin_ids))
    
    admin_router.include_router(panel.router)
    admin_router.include_router(user_management.router)
    admin_router.include_router(promos.router)
    admin_router.include_router(price_control.router)
    admin_router.include_router(settings.router)
    admin_router.include_router(broadcast.router)
    admin_router.include_router(fragment_status.router)
    # Добавляем роутер с командой
    admin_router.include_router(router)
    return admin_router