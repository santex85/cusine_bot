from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from loader import db
from states.user_mode_state import UserModeState
from states.sos_state import SosState
from keyboards.default.markups import cancel_message, cancel_markup, user_main_menu

router = Router()

@router.message(F.text == '❓ SOS', UserModeState.USER)
async def process_sos(message: types.Message, state: FSMContext):
    """
    Начинает процесс сбора вопроса от пользователя.
    """
    await state.set_state(SosState.question)
    await message.answer(
        "Напишите ваш вопрос или проблему, и мы постараемся помочь.",
        reply_markup=cancel_markup()
    )


@router.message(SosState.question, F.text == cancel_message)
async def cancel_sos_handler(message: types.Message, state: FSMContext):
    """
    Отменяет процесс отправки вопроса.
    """
    await state.clear()
    await message.answer("Отменено.", reply_markup=user_main_menu())


@router.message(SosState.question)
async def process_question_text(message: types.Message, state: FSMContext):
    """
    Принимает вопрос, сохраняет его в базу данных.
    """
    user_id = message.from_user.id
    question_text = message.text

    db.query(
        'INSERT INTO questions (cid, question) VALUES (?, ?)',
        (user_id, question_text)
    )

    await state.clear()
    await message.answer(
        "Спасибо! Ваш вопрос был отправлен администратору. Мы скоро с вами свяжемся.",
        reply_markup=user_main_menu()
    )
