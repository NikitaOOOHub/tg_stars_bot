import logging
from aiogram import F, Router, types
from services.repository import Repository
from services.fragment_auth import FragmentAuth
from services.ton_api import get_ton_balance
from config import Config

router = Router()

@router.callback_query(F.data == "admin_fragment_status")
async def fragment_status_callback(call: types.CallbackQuery, repo: Repository, config: Config):
    fragment_auth = FragmentAuth(config)
    
    try:
        auth_status = await fragment_auth.check_auth_status()
        auth_text = "✅ Авторизован" if auth_status else "❌ Не авторизован"
    except Exception as e:
        auth_text = f"❌ Ошибка проверки: {str(e)[:50]}"
    
    try:
        ton_balance, ton_error = await get_ton_balance(config.ton.ton_wallet_address)
        if ton_error:
            ton_balance_text = f"❌ {ton_error[:50]}"
        else:
            ton_balance_text = f"💎 {ton_balance:.4f} TON"
    except Exception as e:
        ton_balance_text = f"❌ Ошибка: {str(e)[:50]}"
    
    try:
        token_refreshed = await fragment_auth.refresh_token_if_needed(repo)
        token_text = "✅ Проверка токена выполнена"
    except Exception as e:
        token_text = f"❌ Ошибка: {str(e)[:50]}"
    
    status_text = (
        f"<b>📊 Статус Fragment</b>\n\n"
        f"<b>Авторизация:</b> {auth_text}\n"
        f"<b>Баланс кошелька:</b> {ton_balance_text}\n"
        f"<b>Токен:</b> {token_text}\n\n"
        f"<b>Адрес кошелька:</b>\n<code>{config.ton.ton_wallet_address}</code>"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_fragment_status")],
        [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")]
    ])
    
    try:
        await call.message.edit_text(status_text, reply_markup=kb)
    except Exception as e:
        if "message is not modified" in str(e):
            await call.answer("Статус уже актуален", show_alert=False)
        else:
            await call.answer("Ошибка обновления статуса", show_alert=True)
