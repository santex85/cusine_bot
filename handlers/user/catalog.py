from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from loader import db, bot
from states.user_mode_state import UserModeState
from keyboards.inline.categories import categories_markup, CategoryCallbackFactory
from keyboards.inline.products_from_catalog import product_markup, CatalogProductCallbackFactory
from aiogram.exceptions import TelegramBadRequest  # Правильный импорт

router = Router()

@router.message(F.text == '🛍️ Каталог', UserModeState.USER)
async def process_catalog(message: types.Message, state: FSMContext):
    """
    Показывает inline-клавиатуру с категориями товаров.
    """
    await message.answer(
        'Выберите раздел, чтобы вывести список товаров:',
        reply_markup=categories_markup()
    )

@router.callback_query(CategoryCallbackFactory.filter(F.action == 'view'), UserModeState.USER)
async def category_callback_handler(query: types.CallbackQuery, callback_data: CategoryCallbackFactory, state: FSMContext):
    """
    Обрабатывает выбор категории. Показывает товары из этой категории.
    """
    # Получаем товары, которых еще нет в корзине пользователя
    products = db.fetchall('''SELECT * FROM products product
    WHERE product.tag = (SELECT title FROM categories WHERE idx=?) 
    AND product.idx NOT IN (SELECT idx FROM cart WHERE cid = ?)''',
                           (callback_data.id, query.from_user.id))
    
    await query.answer('Все доступные товары.')
    await show_products(query.message, products)

@router.callback_query(CatalogProductCallbackFactory.filter(F.action == 'add'), UserModeState.USER)
async def add_product_callback_handler(query: types.CallbackQuery, callback_data: CatalogProductCallbackFactory, state: FSMContext):
    """
    Добавляет товар в корзину.
    """
    db.query('INSERT INTO cart VALUES (?, ?, 1)', (query.from_user.id, callback_data.id))
    await query.answer('Товар добавлен в корзину!')
    # Удаляем сообщение с товаром, чтобы избежать повторного добавления
    try:
        await query.message.delete()
    except TelegramBadRequest: # Используем правильное исключение
        pass # Ничего страшного, если сообщение уже удалено

async def show_products(message: types.Message, products: list):
    """
    Отправляет пользователю список товаров.
    """
    if not products:
        await message.answer('Здесь ничего нет 😢')
    else:
        for idx, title, body, image, price, _ in products:
            markup = product_markup(idx, price)
            caption = f"""<b>{title}</b>

{body}

Цена: {price}₽."""
            await message.answer_photo(
                photo=image,
                caption=caption,
                reply_markup=markup
            )
