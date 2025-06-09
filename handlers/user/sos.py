from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from keyboards.default.markups import all_right_message, cancel_message, submit_markup
from aiogram.types import Message
from states import SosState
# Удален import IsUser
from loader import dp, db
from states.user_mode_state import UserModeState # Добавлен импорт UserModeState


# Обработчик для команды /sos - срабатывает только в состоянии USER
@dp.message_handler(commands='sos', state=UserModeState.USER) # Добавлен фильтр state
async def cmd_sos(message: Message, state: FSMContext): # Добавлен state
    await SosState.question.set()
    await message.answer('В чем суть проблемы? Опишите как можно детальнее и администратор обязательно вам ответит.', reply_markup=ReplyKeyboardRemove())


# Остальные обработчики в этом файле уже используют состояния из SosState
# и не требуют дополнительного фильтра по UserModeState.

@dp.message_handler(state=SosState.question)
async def process_question(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['question'] = message.text

    await message.answer('Убедитесь, что все верно.', reply_markup=submit_markup())
    await SosState.next()


@dp.message_handler(lambda message: message.text not in [cancel_message, all_right_message], state=SosState.submit)
async def process_price_invalid(message: Message, state: FSMContext): # Добавлен state (если нужен внутри функции)
    await message.answer('Такого варианта не было.')


@dp.message_handler(text=cancel_message, state=SosState.submit)
async def process_cancel(message: Message, state: FSMContext):
    await message.answer('Отменено!', reply_markup=ReplyKeyboardRemove())
    await state.finish()
    # После отмены, пользователь должен вернуться в основное состояние USER
    await UserModeState.USER.set()


@dp.message_handler(text=all_right_message, state=SosState.submit)
async def process_submit(message: Message, state: FSMContext):

    cid = message.chat.id

    # TODO: Возможно, отправить вопрос администраторам тут?
    # Можно использовать функцию из handlers.admin.notifications
    # Например: await send_new_question_notification(bot, ADMINS, cid, data['question'])

    if db.fetchone('SELECT * FROM questions WHERE cid=?', (cid,)) == None:

        async with state.proxy() as data:
            db.query('INSERT INTO questions VALUES (?, ?)',
                     (cid, data['question']))

        await message.answer('Отправлено!', reply_markup=ReplyKeyboardRemove())

    else:

        await message.answer('Превышен лимит на количество задаваемых вопросов.', reply_markup=ReplyKeyboardRemove())

    await state.finish()
    # После завершения, пользователь должен вернуться в основное состояние USER
    await UserModeState.USER.set()
