from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from loader import db, bot
from keyboards.default.markups import (
    cancel_markup, back_markup, check_markup,
    all_right_message, back_message, cancel_message
)
from states import ProductState, CategoryState
from hashlib import md5
from states.user_mode_state import UserModeState
from keyboards.inline.categories import CategoryCallbackFactory
from aiogram.exceptions import TelegramBadRequest

router = Router()

# --- Добавление категории ---

@router.callback_query(F.data == 'add_category', UserModeState.ADMIN)
async def add_category_handler(query: CallbackQuery, state: FSMContext):
    await query.message.delete()
    await query.message.answer('Введите название новой категории:', reply_markup=cancel_markup())
    await state.set_state(CategoryState.title)

@router.message(CategoryState.title, F.text != cancel_message)
async def set_category_title_handler(message: Message, state: FSMContext):
    category_name = message.text
    idx = md5(category_name.encode('utf-8')).hexdigest()
    db.query('INSERT INTO categories (idx, title) VALUES (?, ?)', (idx, category_name))
    
    await message.answer(f'Категория "{category_name}" успешно добавлена.', reply_markup=ReplyKeyboardRemove())
    await state.clear()
    from .menu import process_settings
    await process_settings(message, state)

@router.message(CategoryState.title, F.text == cancel_message)
async def cancel_category_handler(message: Message, state: FSMContext):
    await message.answer("Отменено.", reply_markup=ReplyKeyboardRemove())
    await state.clear()
    from .menu import process_settings
    await process_settings(message, state)


# --- Просмотр и удаление товаров в категории ---

@router.callback_query(CategoryCallbackFactory.filter(F.action == 'view'), UserModeState.ADMIN)
async def view_products_in_category(query: CallbackQuery, callback_data: CategoryCallbackFactory, state: FSMContext):
    # ... (код без изменений)
    pass

@router.callback_query(F.data.startswith('delete_product_'))
async def delete_product_handler(query: CallbackQuery, state: FSMContext):
    # ... (код без изменений)
    pass


# --- Удаление категории ---

@router.message(F.text == '🗑️ Удалить эту категорию', UserModeState.ADMIN)
async def delete_category_handler(message: Message, state: FSMContext):
    # ... (код без изменений)
    pass

# --- Возврат к списку категорий ---
@router.message(F.text == '⬅️ Назад к категориям', UserModeState.ADMIN)
async def back_to_categories(message: Message, state: FSMContext):
     await message.answer('Возвращаемся к списку категорий...', reply_markup=ReplyKeyboardRemove())
     await state.clear()
     from .menu import process_settings
     await process_settings(message, state)


# =================================================================
# --- МАШИНА СОСТОЯНИЙ ДЛЯ ДОБАВЛЕНИЯ ТОВАРА ---
# =================================================================

# 1. Начало
@router.message(F.text == '➕ Добавить товар в эту категорию', UserModeState.ADMIN)
async def add_product_start(message: Message, state: FSMContext):
    await message.answer('Введите название товара:', reply_markup=cancel_markup())
    await state.set_state(ProductState.title)

# Отмена на любом шаге
@router.message(F.text == cancel_message, ProductState)
async def cancel_add_product(message: Message, state: FSMContext):
    await message.answer('Добавление товара отменено.', reply_markup=ReplyKeyboardRemove())
    await state.clear()
    from .menu import process_settings
    await process_settings(message, state)

# 2. Получение названия
@router.message(ProductState.title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer('Теперь введите описание товара:', reply_markup=back_markup())
    await state.set_state(ProductState.body)

# 3. Получение описания
@router.message(ProductState.body)
async def process_body(message: Message, state: FSMContext):
    await state.update_data(body=message.text)
    await message.answer('Отправьте фото товара:', reply_markup=back_markup())
    await state.set_state(ProductState.image)

# 4. Получение фото
@router.message(ProductState.image, F.photo)
async def process_image(message: Message, state: FSMContext):
    # В aiogram 3 рекомендуется сохранять file_id, а не скачивать файл
    image_file_id = message.photo[-1].file_id
    await state.update_data(image=image_file_id)
    await message.answer('Теперь введите цену (только цифры):', reply_markup=back_markup())
    await state.set_state(ProductState.price)

# 5. Получение цены
@router.message(ProductState.price, lambda msg: msg.text.isdigit())
async def process_price(message: Message, state: FSMContext):
    await state.update_data(price=int(message.text))
    
    # Показываем превью
    data = await state.get_data()
    title = data.get("title")
    body = data.get("body")
    price = data.get("price")
    image = data.get("image")
    
    caption = f"""<b>{title}</b>

{body}

Цена: {price}₽."""
    await message.answer_photo(
        photo=image,
        caption=caption,
        reply_markup=check_markup()
    )
    await state.set_state(ProductState.confirm)

# 6. Подтверждение и сохранение
@router.message(ProductState.confirm, F.text == all_right_message)
async def process_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    category_title = data.get('category_title')
    
    # Генерируем ID и сохраняем в БД
    idx = md5(' '.join([
        data.get('title'), 
        data.get('body'), 
        str(data.get('price')), 
        category_title
    ]).encode('utf-8')).hexdigest()
    
    db.query('INSERT INTO products (idx, title, body, image, price, tag) VALUES (?, ?, ?, ?, ?, ?)',
             (idx, data.get('title'), data.get('body'), data.get('image'), data.get('price'), category_title))
             
    await message.answer("Товар успешно добавлен!", reply_markup=ReplyKeyboardRemove())
    await state.clear()
    from .menu import process_settings
    await process_settings(message, state)

# Обработка некорректных вводов
@router.message(ProductState.price)
async def process_price_invalid(message: Message):
    await message.answer("Вы ввели не число. Пожалуйста, введите цену цифрами.")

@router.message(ProductState.image)
async def process_image_invalid(message: Message):
    await message.answer("Пожалуйста, отправьте фото.")

# Обработка кнопок "Назад" (упрощенно - сбрасывает на начало)
@router.message(F.text == back_message, ProductState)
async def process_back(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == ProductState.body:
        await state.set_state(ProductState.title)
        await message.answer("Вы вернулись к вводу названия. Введите его заново.")
    # и т.д. для других состояний, пока для простоты сбрасываем
    else:
        await state.clear()
        await message.answer("Вы отменили добавление товара.", reply_markup=ReplyKeyboardRemove())
        from .menu import process_settings
        await process_settings(message, state)
