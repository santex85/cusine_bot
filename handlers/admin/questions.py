from handlers.user.menu import questions
from aiogram.dispatcher import FSMContext
from aiogram.utils.callback_data import CallbackData
from keyboards.default.markups import all_right_message, cancel_message, submit_markup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.types.chat import ChatActions
from states import AnswerState
from loader import dp, db, bot
# Удален import IsAdmin
from states.user_mode_state import UserModeState # Добавлен импорт UserModeState

question_cb = CallbackData('question', 'cid', 'action')


# Обработчик для кнопки '❓ Вопросы' - срабатывает только в состоянии ADMIN
@dp.message_handler(text=questions, state=UserModeState.ADMIN) # Изменен фильтр
async def process_questions(message: Message, state: FSMContext): # Добавлен state

    await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    questions = db.fetchall('SELECT * FROM questions')

    if len(questions) == 0:

        await message.answer('Нет вопросов.')

    else:

        for cid, question in questions:

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(
                'Ответить', callback_data=question_cb.new(cid=cid, action='answer')))

            await message.answer(question, reply_markup=markup)


# Обработчик для колбэка 'Ответить' - срабатывает только в состоянии ADMIN
@dp.callback_query_handler(question_cb.filter(action='answer'), state=UserModeState.ADMIN) # Изменен фильтр
async def process_answer(query: CallbackQuery, callback_data: dict, state: FSMContext):

    async with state.proxy() as data:
        data['cid'] = callback_data['cid']

    await query.message.answer('Напиши ответ.', reply_markup=ReplyKeyboardRemove())
    await AnswerState.answer.set()


# Обработчик ввода ответа - срабатывает только в состоянии AnswerState.answer
# Не требует дополнительного фильтра по UserModeState
@dp.message_handler(state=AnswerState.answer)
async def process_submit(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data['answer'] = message.text

    await AnswerState.next()
    await message.answer('Убедитесь, что не ошиблись в ответе.', reply_markup=submit_markup())


# Обработчик кнопки отмены на этапе submit - срабатывает только в состоянии AnswerState.submit
# Не требует дополнительного фильтра по UserModeState
@dp.message_handler(text=cancel_message, state=AnswerState.submit)
async def process_send_answer_cancel(message: Message, state: FSMContext): # Переименован для уникальности
    await message.answer('Отменено!', reply_markup=ReplyKeyboardRemove())
    await state.finish()
    # После отмены, пользователь должен вернуться в основное состояние ADMIN
    await UserModeState.ADMIN.set()


# Обработчик кнопки подтверждения на этапе submit - срабатывает только в состоянии AnswerState.submit
# Не требует дополнительного фильтра по UserModeState
@dp.message_handler(text=all_right_message, state=AnswerState.submit)
async def process_send_answer_confirm(message: Message, state: FSMContext): # Переименован для уникальности

    async with state.proxy() as data:

        answer = data['answer']
        cid = data['cid']

        question = db.fetchone(
            'SELECT question FROM questions WHERE cid=?', (cid,))[0]
        db.query('DELETE FROM questions WHERE cid=?', (cid,))
        text = f'Вопрос: <b>{question}</b>Ответ: <b>{answer}</b>'

        await message.answer('Отправлено!', reply_markup=ReplyKeyboardRemove())
        await bot.send_message(cid, text)

    await state.finish()
    # После завершения, пользователь должен вернуться в основное состояние ADMIN
    await UserModeState.ADMIN.set()
