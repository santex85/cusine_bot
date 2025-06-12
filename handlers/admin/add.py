from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from loader import db
from keyboards.default.markups import (
    cancel_markup, back_markup, check_markup,
    all_right_message, back_message, cancel_message
)
from states import ProductState
from states.category_state import CategoryState # Обновленный импорт
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
    # Проверяем, существует ли категория с таким названием
    if db.fetchone('SELECT 1 FROM categories WHERE title = ?', (category_name,)):
        await message.answer(f'Категория "{category_name}" уже существует.')
        return
        
    db.query('INSERT INTO categories (idx, title) VALUES (?, ?)', (idx, category_name))
    
    await message.answer(f'Категория "{category_name}" успешно добавлена.', reply_markup=ReplyKeyboardRemove())
    await state.clear()
    # Возвращаемся к меню настроек
    from .menu import process_settings
    await process_settings(message, state)


@router.message(CategoryState.title, F.text == cancel_message)
async def cancel_category_handler(message: Message, state: FSMContext):
    await message.answer("Отменено.", reply_markup=ReplyKeyboardRemove())
    await state.clear()
    from .menu import process_settings
    await process_settings(message, state)


# --- Просмотр и управление категорией ---

def category_management_markup():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='➕ Добавить товар в эту категорию')],
            [KeyboardButton(text='🗑️ Удалить эту категорию')],
            [KeyboardButton(text='⬅️ Назад к категориям')]
        ],
        resize_keyboard=True
    )

@router.callback_query(CategoryCallbackFactory.filter(F.action == 'view'), UserModeState.ADMIN)
async def view_products_in_category(query: types.CallbackQuery, callback_data: CategoryCallbackFactory, state: FSMContext):
    category_id = callback_data.id
    category_info = db.fetchone('SELECT title FROM categories WHERE idx = ?', (category_id,))
    
    if not category_info:
        await query.answer("Категория не найдена.", show_alert=True)
        return

    category_name = category_info[0]

    # Сохраняем контекст категории в состояние
    await state.update_data(category_id=category_id, category_name=category_name)
    await state.set_state(CategoryState.viewing)
    
    await query.message.delete()
    # TODO: В будущем здесь будет вывод списка товаров
    await query.message.answer(
        f'Вы в категории: <b>{category_name}</b>',
        reply_markup=category_management_markup()
    )
    await query.answer()


# --- Удаление категории ---

@router.message(F.text == '🗑️ Удалить эту категорию', CategoryState.viewing)
async def delete_category_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    category_id = data.get('category_id')
    category_name = data.get('category_name')

    # Безопасность: удаляем связанные товары
    db.query('DELETE FROM products WHERE tag = ?', (category_id,))
    db.query('DELETE FROM categories WHERE idx = ?', (category_id,))
    
    await message.answer(
        f'Категория <b>{category_name}</b> и все товары в ней были удалены.',
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()
    from .menu import process_settings
    await process_settings(message, state)


# --- Возврат к списку категорий ---
@router.message(F.text == '⬅️ Назад к категориям', CategoryState.viewing)
async def back_to_categories(message: types.Message, state: FSMContext):
     await message.answer('Возвращаемся к списку категорий...', reply_markup=ReplyKeyboardRemove())
     await state.clear()
     from .menu import process_settings
     await process_settings(message, state)


# =================================================================
# --- МАШИНА СОСТОЯНИЙ ДЛЯ ДОБАВЛЕНИЯ ТОВАРА ---
# =================================================================

# 1. Начало
@router.message(F.text == '➕ Добавить товар в эту категорию', CategoryState.viewing)
async def add_product_start(message: Message, state: FSMContext):
    await message.answer('Введите название товара:', reply_markup=cancel_markup())
    await state.set_state(ProductState.title)

# Отмена на любом шаге
@router.message(F.text == cancel_message, ProductState)
async def cancel_add_product(message: Message, state: FSMContext):
    # Восстанавливаем состояние просмотра категории
    data = await state.get_data()
    category_name = data.get('category_name', 'текущую')
    await state.set_state(CategoryState.viewing)
    await message.answer(f'Добавление товара отменено. Вы все еще в категории <b>{category_name}</b>.', 
                         reply_markup=category_management_markup())


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
    image_file_id = message.photo[-1].file_id
    await state.update_data(image=image_file_id)
    await message.answer('Теперь введите цену (только цифры):', reply_markup=back_markup())
    await state.set_state(ProductState.price)

# 5. Получение цены
@router.message(ProductState.price, lambda msg: msg.text.isdigit())
async def process_price(message: Message, state: FSMContext):
    await state.update_data(price=int(message.text))
    
    data = await state.get_data()
    caption = f"""<b>{data.get("title")}</b>

{data.get("body")}

Цена: {data.get("price")}₽."""

    await message.answer_photo(
        photo=data.get("image"),
        caption=caption,
        reply_markup=check_markup()
    )
    await state.set_state(ProductState.confirm)

# 6. Подтверждение и сохранение
@router.message(ProductState.confirm, F.text == all_right_message)
async def process_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    category_id = data.get('category_id') # Получаем ID категории из состояния
    
    if not category_id:
        await message.answer("Ошибка: не удалось определить категорию. Попробуйте снова.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    # Генерируем ID и сохраняем в БД
    idx = md5(f"{data.get('title')}{data.get('body')}{data.get('price')}".encode('utf-8')).hexdigest()
    
    db.query('INSERT INTO products (idx, title, body, photo, price, tag) VALUES (?, ?, ?, ?, ?, ?)',
             (idx, data.get('title'), data.get('body'), data.get('image'), data.get('price'), category_id)) # Используем category_id
             
    await message.answer("Товар успешно добавлен!", reply_markup=category_management_markup())
    # Возвращаемся в состояние просмотра категории
    await state.set_state(CategoryState.viewing)


# Обработка некорректных вводов
@router.message(ProductState.price)
async def process_price_invalid(message: Message):
    await message.answer("Вы ввели не число. Пожалуйста, введите цену цифрами.")

@router.message(ProductState.image)
async def process_image_invalid(message: Message):
    await message.answer("Пожалуйста, отправьте фото.")

# Обработка кнопок "Назад" 
@router.message(F.text == back_message, ProductState)
async def process_back(message: Message, state: FSMContext):
    current_state = await state.get_state()
    
    if current_state == ProductState.body:
        await state.set_state(ProductState.title)
        await message.answer("Вы вернулись к вводу названия. Введите его заново.", reply_markup=cancel_markup())
    elif current_state == ProductState.image:
        await state.set_state(ProductState.body)
        await message.answer("Вы вернулись к вводу описания. Введите его заново.", reply_markup=back_markup())
    elif current_state == ProductState.price:
        await state.set_state(ProductState.image)
        await message.answer("Вы вернулись к отправке фото. Отправьте его заново.", reply_markup=back_markup())
    else: # На шаге подтверждения и на первом шаге "назад" работает как отмена
        data = await state.get_data()
        category_name = data.get('category_name', 'текущую')
        await state.set_state(CategoryState.viewing)
        await message.answer(f'Добавление товара отменено. Вы все еще в категории <b>{category_name}</b>.', 
                             reply_markup=category_management_markup())
