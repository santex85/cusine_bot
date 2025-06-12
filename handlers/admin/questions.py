from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from loader import db
from states.user_mode_state import UserModeState
from aiogram.filters.callback_data import CallbackData
from data.config import ADMINS # Импортируем список админов

class QuestionCallbackFactory(CallbackData, prefix="question"):
    action: str  # "answer" или "delete"
    user_id: int
    question_id: int

def get_question_markup(user_id: int, question_id: int):
    return types.InlineKeyboardMarkup(
        inline_keyboard=[[
            types.InlineKeyboardButton(text="Ответить", callback_data=QuestionCallbackFactory(action="answer", user_id=user_id, question_id=question_id).pack()),
            types.InlineKeyboardButton(text="Удалить", callback_data=QuestionCallbackFactory(action="delete", user_id=user_id, question_id=question_id).pack())
        ]]
    )

router = Router()

ANSWER_STATE_PREFIX = "answer_to_"

@router.message(F.text == '❓ Вопросы', UserModeState.ADMIN)
async def process_questions(message: types.Message):
    """
    Показывает администратору список вопросов от пользователей.
    """
    await message.answer("Загрузка вопросов...")
    
    questions = db.fetchall("SELECT rowid, cid, question FROM questions ORDER BY rowid ASC")

    if not questions:
        await message.answer("Новых вопросов нет.")
        return

    await message.answer("<b>Новые вопросы:</b>")
    for q_id, user_id, q_text in questions:
        text = f"""<b>Вопрос №{q_id} от пользователя {user_id}</b>

<i>«{q_text}»</i>"""
        markup = get_question_markup(user_id, q_id)
        await message.answer(text, reply_markup=markup)

@router.callback_query(QuestionCallbackFactory.filter(F.action == "delete"))
async def delete_question_handler(query: types.CallbackQuery, callback_data: QuestionCallbackFactory):
    db.query("DELETE FROM questions WHERE rowid = ?", (callback_data.question_id,))
    await query.answer("Вопрос удален.")
    await query.message.delete()

@router.callback_query(QuestionCallbackFactory.filter(F.action == "answer"))
async def answer_question_handler(query: types.CallbackQuery, callback_data: QuestionCallbackFactory, state: FSMContext):
    await state.set_state(f"{ANSWER_STATE_PREFIX}{callback_data.user_id}")
    await query.message.answer(
        f"Введите ответ для пользователя {callback_data.user_id}. "
        "Все, что вы напишете, будет переслано ему. Для отмены введите /cancel."
    )
    await query.answer()

@router.message(F.text == "/cancel", lambda msg: str(msg.from_user.id) in ADMINS)
async def cancel_answer_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state and current_state.startswith(ANSWER_STATE_PREFIX):
        await state.clear()
        await message.answer("Ответ отменен.")

@router.message(lambda msg: str(msg.from_user.id) in ADMINS)
async def send_answer_to_user(message: types.Message, state: FSMContext, bot: Bot):
    current_state = await state.get_state()
    if not (current_state and current_state.startswith(ANSWER_STATE_PREFIX)):
        # Этот обработчик не должен срабатывать, если админ не в состоянии ответа
        # Он будет ловить все сообщения от админа, не попавшие в другие хендлеры.
        # Это нужно будет исправить более строгой фильтрацией в app.py
        # или изменением порядка регистрации роутеров.
        # Пока что оставляем так для базовой функциональности.
        return

    try:
        user_id_to_answer = int(current_state.split(ANSWER_STATE_PREFIX)[1])
        await bot.copy_message(chat_id=user_id_to_answer, from_chat_id=message.chat.id, message_id=message.message_id)
        await message.answer(f"✅ Сообщение отправлено пользователю {user_id_to_answer}.")
    except Exception as e:
        await message.answer(f"Не удалось отправить сообщение: {e}")
    finally:
        await state.clear()
