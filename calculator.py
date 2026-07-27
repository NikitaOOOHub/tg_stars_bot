from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from services.repository import Repository
from keyboards import user_kb
from states.user import CalculatorStates
from utils.safe_message import safe_answer_photo, safe_delete_message
from config import Config
from utils.prices import calculate_stars_price

router = Router()

@router.callback_query(F.data == "calculator")
async def calculator_menu_callback(call: types.CallbackQuery, state: FSMContext, config: Config):
    await state.clear()
    await safe_delete_message(call)
    await safe_answer_photo(
        call,
        photo=config.visuals.img_url_calculator,
        caption="<b>🧮 Калькулятор</b>\n\nВыберите, как вы хотите рассчитать стоимость:",
        reply_markup=user_kb.get_calculator_kb()
    )

@router.callback_query(F.data == "calc_by_stars")
async def calc_by_stars_start(call: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="⬅️ Назад", callback_data="calculator")]])
    await call.message.edit_caption(caption="Введите количество звезд (минимум 50):", reply_markup=kb)
    await state.set_state(CalculatorStates.waiting_for_stars_amount)

@router.message(CalculatorStates.waiting_for_stars_amount)
async def calc_by_stars_process(message: types.Message, state: FSMContext, repo: Repository):
    try:
        stars_amount = int(message.text)
        if stars_amount < 50:
            await message.answer("❗️ Минимальное количество для расчета — 50 звёзд.")
            return
    except ValueError:
        await message.answer("❗️ Пожалуйста, введите целое число.")
        return

    total_cost = calculate_stars_price(stars_amount)
    await message.answer(f"⭐ <b>{stars_amount:,}</b> звёзд ≈ <b>{total_cost:.2f} ₽</b>")
    await state.clear()

@router.callback_query(F.data == "calc_by_rub")
async def calc_by_rub_start(call: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="⬅️ Назад", callback_data="calculator")]])
    await call.message.edit_caption(caption="Введите сумму в рублях (₽):", reply_markup=kb)
    await state.set_state(CalculatorStates.waiting_for_rub_amount)

@router.message(CalculatorStates.waiting_for_rub_amount)
async def calc_by_rub_process(message: types.Message, state: FSMContext, repo: Repository):
    try:
        rub_amount = float(message.text.replace(",", "."))
        if rub_amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❗️ Пожалуйста, введите корректное положительное число.")
        return

    low, high = 50, 1000000
    best = 50
    while low <= high:
        mid = (low + high) // 2
        cost = calculate_stars_price(mid)
        if cost <= rub_amount:
            best = mid
            low = mid + 1
        else:
            high = mid - 1
    stars_count = best

    await message.answer(f"₽ <b>{rub_amount:.2f}</b> ≈ <b>{stars_count:,} ⭐</b>")
    await state.clear()