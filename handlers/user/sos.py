from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from keyboards.default.markups import all_right_message, cancel_message, submit_markup
from aiogram.types import Message
from states import SosState
from loader import dp, db, bot
from states.user_mode_state import UserModeState

@dp.message_handler(commands='sos', state=UserModeState.USER)
async def cmd_sos(message: Message, state: FSMContext):
    await state.set_state(SosState.question)
    await bot.send_message(message.chat.id, 'В чем суть проблемы? Опишите как можно детальнее и администратор обязательно вам ответит.', reply_markup=ReplyKeyboardRemove())

@dp.message_handler(state=SosState.question)
async def process_question(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['question'] = message.text
    await bot.send_message(message.chat.id, 'Убедитесь, что все верно.', reply_markup=submit_markup())
    await state.set_state(SosState.next())

@dp.message_handler(lambda message: message.text not in [cancel_message, all_right_message], state=SosState.submit)
async def process_price_invalid(message: Message, state: FSMContext):
    await bot.send_message(message.chat.id, 'Такого варианта не было.')

@dp.message_handler(text=cancel_message, state=SosState.submit)
async def process_cancel(message: Message, state: FSMContext):
    await bot.send_message(message.chat.id, 'Отменено!', reply_markup=ReplyKeyboardRemove())
    await state.finish()
    await state.set_state(UserModeState.USER)

@dp.message_handler(text=all_right_message, state=SosState.submit)
async def process_submit(message: Message, state: FSMContext):
    cid = message.chat.id
    if db.fetchone('SELECT * FROM questions WHERE cid=?', (cid,)) is None:
        async with state.proxy() as data:
            db.query('INSERT INTO questions VALUES (?, ?)',
                     (cid, data['question']))
        await bot.send_message(message.chat.id, 'Отправлено!', reply_markup=ReplyKeyboardRemove())
    else:
        await bot.send_message(message.chat.id, 'Превышен лимит на количество задаваемых вопросов.', reply_markup=ReplyKeyboardRemove())
    await state.finish()
    await state.set_state(UserModeState.USER)
