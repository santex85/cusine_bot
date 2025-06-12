from handlers.admin.menu import questions
from aiogram.dispatcher import FSMContext
from aiogram.utils.callback_data import CallbackData
from keyboards.default.markups import all_right_message, cancel_message, submit_markup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.types.chat import ChatActions
from states import AnswerState
from loader import dp, db, bot
from states.user_mode_state import UserModeState

question_cb = CallbackData('question', 'cid', 'action')

@dp.message_handler(text=questions, state=UserModeState.ADMIN)
async def process_questions(message: Message, state: FSMContext):
    await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    questions = db.fetchall('SELECT * FROM questions')
    if len(questions) == 0:
        await bot.send_message(message.chat.id, 'Нет вопросов.')
    else:
        for cid, question in questions:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(
                'Ответить', callback_data=question_cb.new(cid=cid, action='answer')))
            await bot.send_message(message.chat.id, question, reply_markup=markup)

@dp.callback_query_handler(question_cb.filter(action='answer'), state=UserModeState.ADMIN)
async def process_answer(query: CallbackQuery, callback_data: dict, state: FSMContext):
    async with state.proxy() as data:
        data['cid'] = callback_data['cid']
    await bot.send_message(query.message.chat.id, 'Напиши ответ.', reply_markup=ReplyKeyboardRemove())
    await AnswerState.answer.set()

@dp.message_handler(state=AnswerState.answer)
async def process_submit(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['answer'] = message.text
    await AnswerState.next()
    await bot.send_message(message.chat.id, 'Убедитесь, что не ошиблись в ответе.', reply_markup=submit_markup())

@dp.message_handler(text=cancel_message, state=AnswerState.submit)
async def process_send_answer_cancel(message: Message, state: FSMContext):
    await bot.send_message(message.chat.id, 'Отменено!', reply_markup=ReplyKeyboardRemove())
    await state.finish()
    await UserModeState.ADMIN.set()

@dp.message_handler(text=all_right_message, state=AnswerState.submit)
async def process_send_answer_confirm(message: Message, state: FSMContext):
    async with state.proxy() as data:
        answer = data['answer']
        cid = data['cid']
        question = db.fetchone(
            'SELECT question FROM questions WHERE cid=?', (cid,))[0]
        db.query('DELETE FROM questions WHERE cid=?', (cid,))
        text = f'Вопрос: <b>{question}</b>Ответ: <b>{answer}</b>'
        await bot.send_message(message.chat.id, 'Отправлено!', reply_markup=ReplyKeyboardRemove())
        await bot.send_message(cid, text)
    await state.finish()
    await UserModeState.ADMIN.set()
