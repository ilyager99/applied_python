from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, FSInputFile
from aiogram.filters import Command
import matplotlib.pyplot as plt
from state import User, Food, Workout
from config import API_WET, API_TR
from aiohttp import ClientSession
import random
import requests
import re

router = Router()
API_KEY = API_WET
API_TRAIN = API_TR


# Обработчик команды /start
@router.message(Command('start'))
async def cmd_start(message: Message):
    welcome_message = await message.reply(
        f'<b>️🏋️‍♂️Здравствуйте! Я ваш персональный тренер по фитнесу.</b>🧘‍♂️\n'
        '\nВведите /help, чтобы узнать больше о моих возможностях.\n\n'
        'Чтобы начать работу, пожалуйста, создайте свой профиль.',
        parse_mode='HTML'
    )
    # Автоматически вызываем команду show_keyboard
    await show_keyboard(welcome_message)


# Обработчик команды /help
@router.message(Command('help'))
async def cmd_help(message: Message):
    help_message = await message.reply(
        '<u>Мои ключевые функции:</u>\n\n'
        '1. <b>Создать аккаунт</b> - Заведение профиля пользователя.\n'
        '2. <b>Аккаунт</b> - Просмотр информации о своем профиле.\n'
        '3. <b>Гидратация</b> - Учет выпитой жидкости и показ оставшегося до нормы.\n'
        '4. <b>Питание</b> - Информация о потребленных калориях за день.\n'
        '5. <b>Тренировочный процесс</b> - Учет сожженных калорий.\n'
        '6. <b>Результаты</b> - Отображение прогресса по жидкости и калориям.',
        parse_mode='HTML'
    )
    # Автоматически вызываем команду show_keyboard
    await show_keyboard(help_message)


# Обработчик команды /keyboard с кнопками
async def show_keyboard(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Создать аккаунт', callback_data='profile'),
                InlineKeyboardButton(text='Аккаунт', callback_data='get_profile'),
            ],
            [
                InlineKeyboardButton(text='Гидратация', callback_data='water'),
                InlineKeyboardButton(text='Питание', callback_data='food'),
            ],
            [
                InlineKeyboardButton(text='Тренировочный процесс ️', callback_data='training'),
                InlineKeyboardButton(text='Результаты', callback_data='progress')

            ]
        ]
    )
    await message.bot.edit_message_reply_markup(
        chat_id=message.chat.id,
        message_id=message.message_id,
        reply_markup=keyboard
    )


# Обработчик кнопки
@router.callback_query()
async def handle_callback(callback_query: CallbackQuery, state: FSMContext):
    if callback_query.data == 'profile':
        await start_profile(callback_query.message, state)
    elif callback_query.data == 'get_profile':
        await get_profile(callback_query.message, state)
    elif callback_query.data == 'water':
        await start_water(callback_query.message, state)
    elif callback_query.data == 'food':
        await calories(callback_query.message, state)
    elif callback_query.data == 'training':
        await start_training(callback_query.message, state)
    elif callback_query.data == 'progress':
        await start_progress(callback_query.message, state)
    else:
        await callback_query.message.answer("Неизвестная опция.")


@router.message(Command('profile'))
async def start_profile(message: Message, state: FSMContext):
    # Завершить текущее состояние, если оно есть
    await state.clear()
    await message.answer('<b><u>Вы выбрали кнопку "Создать профиль"</u></b>\n\n'
                         'Назовите Ваше имя?',
                         parse_mode='HTML')
    await state.set_state(User.name)


@router.message(User.name)
async def process_manual_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("Имя не может быть пустым.")
        return
    elif not re.match('^[A-Za-zА-Яа-яЁёs]+$', name):
        await message.answer('Имя должно содержать только буквы.')
        return
    await state.update_data(name=name)
    await message.answer('Ваш возраст?')
    await state.set_state(User.age)


@router.message(User.age)
async def process_age(message: Message, state: FSMContext):
    age = message.text.strip()
    # Проверка корректности возраста
    if not age.isdigit() or not (10 <= int(age) < 100):
        await message.answer('Введите корректный возраст:')
        return
    await state.update_data(age=int(age))
    await message.answer('Укажите свой вес в килограммах:')
    await state.set_state(User.weight)


@router.message(User.weight)
async def process_weight(message: Message, state: FSMContext):
    weight = message.text.strip()
    # Проверка корректности веса
    if not weight.isdigit() or not (30 <= float(weight) <= 500):
        await message.answer('Введите корректный вес:')
        return
    await state.update_data(weight=float(weight))
    await message.answer('Укажите свой рост в сантиметрах:')
    await state.set_state(User.height)


@router.message(User.height)
async def process_height(message: Message, state: FSMContext):
    height = message.text.strip()
    # Проверка корректности роста
    if not height.isdigit() or not (120 <= int(height) <= 300):
        await message.answer('Введите корректный рост:')
        return
    await state.update_data(height=int(height))
    await message.answer('Сколько время вы проводите в движении, напишите в минутах?')
    await state.set_state(User.activity_level)


@router.message(User.activity_level)
async def process_activity_level(message: Message, state: FSMContext):
    activity_level = message.text.strip()
    if not activity_level.isdigit() or not (0 <= int(activity_level) <= 1440):
        await message.answer('Введите корректное кол-во минут:')
        return
    await state.update_data(activity_level=int(activity_level))
    await message.answer('В каком городе вы живете?\n')
    await state.set_state(User.city)


@router.message(User.city)
async def process_city(message: Message, state: FSMContext):
    city = message.text.strip()
    if not re.match('^[A-Za-zs]+$', city):
        await message.answer(
            'Напишите назхвание города английскими буквами.')
        return
    await state.update_data(city=city)
    await message.answer('Какова ваша цель по калориям?\n'
                         '(Нажмите "по умолчанию", чтобы я посчитать калории за Вас)')
    await state.set_state(User.calorie_goal)


async def calculate_calories(data):
    weight = float(data.get("weight", 0))
    height = float(data.get("height", 0))
    age = int(data.get("age", 0))
    activity_level = int(data.get("activity_level", 0))

    # Расчет калорий по формуле
    calories = 10 * weight + 6.25 * height - 5 * age
    # Добавляем уровень активности
    if activity_level < 30:
        calories += 200
    elif activity_level < 60:
        calories += 300
    else:
        calories += 400

    return calories


async def display_user_data(data, calorie_goal, goal_type, message):
    data = await message.answer(f'<b>Ваши данные:</b>\n\n'
                                f'Имя: {data.get("name")}\n'
                                f'Возраст: {data.get("age")} лет\n'
                                f'Вес: {data.get("weight")} кг\n'
                                f'Рост: {data.get("height")} см\n'
                                f'Уровень активности: {data.get("activity_level")} минут в день\n'
                                f'Город: {data.get("city")}\n'
                                f'Цель калорий: {calorie_goal} ккал ({goal_type})', parse_mode='HTML')
    # Возврат в главное меню
    await show_keyboard(data)


@router.message(User.calorie_goal)
async def process_calorie_goal(message: Message, state: FSMContext):
    data = await state.get_data()
    if message.text.lower() == "по умолчанию":
        calories = await calculate_calories(data)
        await state.update_data(custom_calorie_goal=float(calories))
        await display_user_data(data, calories, "по умолчанию", message)
    else:
        custom_calorie_goal = message.text.strip()
        if not custom_calorie_goal.isdigit() or not (800 <= int(custom_calorie_goal) <= 6000):
            await message.answer('Введите верное значение калорий:')
            return
        await state.update_data(custom_calorie_goal=float(custom_calorie_goal))
        await display_user_data(data, message.text, "задано вручную", message)


###################################Profile##############################################
@router.message(Command('get_profile'))
async def get_profile(message: Message, state: FSMContext):
    data = await state.get_data()  # Получаем данные состояния
    if not data.get('name'):
        p = await message.answer('<b><u>Вы выбрали кнопку "Профиль"</u></b>\n\n'
                                 '<b>Ваш профиль пуст.</b> Для просмотра нужно сначала создать профиль.',
                                 parse_mode='HTML')
    else:
        p = await message.answer(
            '<b><u>Вы выбрали кнопку "Профиль"</u></b>\n\n'
            f'<b>Ваши данные:</b>\n\n'
            f'Имя: {data.get("name")}\n'
            f'Возраст: {data.get("age")} лет\n'
            f'Вес: {data.get("weight")} кг\n'
            f'Рост: {data.get("height")} см\n'
            f'Уровень активности: {data.get("activity_level")} минут в день\n'
            f'Город: {data.get("city")}\n'
            f'Цель калорий: {data.get("custom_calorie_goal")} ккал\n'
            f'Количество выпитой воды: {data.get("logged_water", 0)} мл\n'
            f'Количество полученных калорий: +{data.get("logged_calories", 0)} ккал\n'
            f'Количество сожженных калорий: -{data.get("burned_calories", 0)} ккал',
            parse_mode='HTML'
        )
    # Возврат в главное меню
    await show_keyboard(p)

# Функция для получения погоды по API из дз1
async def fetch_temperature(session, city):
    params = {'q': city, 'appid': API_KEY, 'units': 'metric', 'lang': 'ru'}
    async with session.get('https://api.openweathermap.org/data/2.5/weather', params=params) as response:
        if response.status == 200:
            data = await response.json()
            return data['main']['temp']
        else:
            print(f"Ошибка при запросе города {city}: {response.status}")
            return None


async def get_temperature(city):
    async with ClientSession() as session:
        return await fetch_temperature(session, city)


@router.message(Command('water'))
async def start_water(message: Message, state: FSMContext):
    data = await state.get_data()  # Получаем данные состояния
    if not data.get('name'):
        p = await message.answer('<b><u>Вы выбрали кнопку "Вода"</u></b>\n\n'
                                 '<b>Ваш профиль пуст.</b> Сначала нужно создать профиль.',
                                 parse_mode='HTML')
        # Возврат в главное меню
        await show_keyboard(p)
    else:
        await message.answer('<b><u>Вы выбрали кнопку "Вода"</u></b>\n\n'
                             'Сколько воды (в мл) Вы уже выпили сегодня?',
                             parse_mode='HTML')
        await state.set_state(User.logged_water)


async def calculate_water_goal(message: Message, data):
    weight = float(data.get('weight', 0))
    activity = int(data.get('activity', 0))
    city = data.get('city', '')
    logged_water = float(data.get('logged_water', 0))

    base_water_intake = weight * 30  # в мл
    additional_water = 0

    if activity > 0:
        additional_water += (activity // 30) * 500  # 500 мл за каждые 30 минут

    current_temp = await get_temperature(city) if city else None
    if current_temp is not None and current_temp > 25:
        additional_water += 500
    if current_temp is not None and current_temp > 30:
        additional_water += 500

    total_water_goal = base_water_intake + additional_water
    remaining_water = total_water_goal - logged_water
    return current_temp, total_water_goal, remaining_water


def plot_water_intake(message, logged_water, total_water_goal, water_intake_w):
    adjusted_target = int(total_water_goal) + int(water_intake_w)
    categories = ['Воды потребили', 'Норма']
    values = [int(logged_water), adjusted_target]
    colors = ['blue', 'green']

    fig, ax = plt.subplots()
    bars = ax.bar(categories, values, color=colors)  # тут

    # Подписи над столбиками
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, yval, round(yval, 2), ha='center', va='bottom')

    if water_intake_w > 0:
        additional_water_bar = ax.bar('Необходимая норма', int(water_intake_w), bottom=int(total_water_goal),
                                      color='blue',
                                      label='Доп вода')

    # Заголовок и метки
    ax.set_title('Выпитая вода в день')
    ax.set_ylabel('Объем')

    # Добавляем легенду
    if water_intake_w > 0:
        ax.legend(loc='upper right')

    # Сохраняем график файл
    plt.savefig('water_intake.jpg')
    plt.close()


@router.message(User.logged_water)
async def process_logged_water(message: Message, state: FSMContext):
    logged_water = message.text.strip()
    # Проверка корректности возраста
    if not logged_water.isdigit() or not (0 <= int(logged_water) <= 5000):
        await message.answer('Введите корректное значение выпитой воды в мл.')
        return
    await state.update_data(logged_water=int(logged_water))
    data = await state.get_data()
    current_temp, total_water_goal, remaining_water = await calculate_water_goal(message, data)
    water_intake_w = data.get('water_intake_w', 0)
    plot_water_intake(message, logged_water, total_water_goal, water_intake_w)
    if water_intake_w == 0:
        if (int(total_water_goal) - int(logged_water)) == 0:
            photo = await message.answer_photo(photo=FSInputFile('water_intake.jpg', filename='График воды'),
                                               caption=f'Вы употребили {logged_water} мл из требуемых {int(total_water_goal)} мл жидкости.\n'
                                                       f'<b>Поздравляю!</b> Вы достигли своей суточной нормы 💧',
                                               parse_mode='HTML')
        elif (int(total_water_goal) - int(logged_water)) < 0:
            photo = await message.answer_photo(photo=FSInputFile('water_intake.jpg', filename='График воды'),
                                               caption=f'Вы употребили {logged_water} мл из требуемых {int(total_water_goal)} мл жидкости.\n'
                                                       f'<b>Внимание!</b> Вы превысили свою норму 💧', parse_mode='HTML')
        else:
            photo = await message.answer_photo(photo=FSInputFile('water_intake.jpg', filename='График воды'),
                                               caption=f'Вы употребили {logged_water} мл из требуемых {int(total_water_goal)} мл жидкости.\n'
                                                       f'Осталось еще {int(remaining_water)} мл до достижения нормы.')
    else:
        if (int(total_water_goal) + int(water_intake_w) - int(logged_water)) == 0:
            photo = await message.answer_photo(photo=FSInputFile('water_intake.jpg', filename='График воды'),
                                               caption='<b>Отличная тренировка!</b>\n'
                                                       f'Вы употребили {logged_water} мл из требуемых {int(total_water_goal) + int(water_intake_w)} мл жидкости.\n'
                                                       f'<b>Поздравляю!</b> Вы достигли своей суточной нормы 💧',
                                               parse_mode='HTML')
        elif (int(total_water_goal) + int(water_intake_w) - int(logged_water)) < 0:
            photo = await message.answer_photo(photo=FSInputFile('water_intake.jpg', filename='График воды'),
                                               caption='<b>Отличная тренировка!</b>\n'
                                                       f'Вы употребили {logged_water} мл из требуемых {int(total_water_goal) + int(water_intake_w)} мл жидкости.\n'
                                                       f'<b>Внимание!</b> Вы превысили свою норму 💧', parse_mode='HTML')
        else:
            photo = await message.answer_photo(photo=FSInputFile('water_intake.jpg', filename='График воды'),
                                               caption='<b>Отличная тренировка!</b>\n'
                                                       f'Вы употребили {logged_water} мл из требуемых {int(total_water_goal) + int(water_intake_w)} мл жидкости.\n'
                                                       f'Осталось еще {int(total_water_goal) + int(water_intake_w) - int(logged_water)} мл до достижения нормы.',
                                               parse_mode='HTML')
    await show_keyboard(photo)

def get_food_info(product_name):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&search_terms={product_name}&json=true"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        products = data.get('products', [])
        if products:  # Проверяем, есть ли найденные продукты
            first_product = products[0]
            return {
                'name': first_product.get('product_name', 'Неизвестно'),
                'calories': first_product.get('nutriments', {}).get('energy-kcal_100g', 0)
            }
        return None
    print(f"Ошибка: {response.status_code}")
    return None


@router.message(Command('food'))
async def calories(message: Message, state: FSMContext):
    data = await state.get_data()  # Получаем данные состояния
    if not data.get('name'):
        p = await message.answer('<b><u>Вы выбрали кнопку "Еда"</u></b>\n\n'
                                 '<b>Ваш профиль пуст.</b> Сначала нужно создать профиль.',
                                 parse_mode='HTML')
        await show_keyboard(p)
    else:
        await message.answer(
            '<b><u>Вы выбрали кнопку "Еда"</u></b>\n\n'
            'Напишите название продукта, чтобы узнать его калорийность.',
            parse_mode='HTML'
        )
        await state.set_state(Food.product)


@router.message(Food.product)
async def process_product_input(message: Message, state: FSMContext):
    product = message.text.strip()
    if not product:
        await message.answer("Название продукта не может быть пустым.")
        return
    elif not re.match('^[A-Za-zА-Яа-яЁёs ]+$', product):
        await message.answer(
            'Название продукта должно содержать только буквы.')
        return

    await state.update_data(product=product)

    food_info = get_food_info(product)
    if food_info is None:
        await message.answer("Продукт не найден. Попробуйте еще раз.")
        return

    product_name = food_info['name']
    calories_per_100g = food_info['calories']

    await message.answer(
        f"{product_name} — {calories_per_100g} ккал на 100 г.\n"
        f"Сколько Вы съели?"
    )
    await state.set_state(Food.gram)
    await state.update_data(calories_per_100g=calories_per_100g)


@router.message(Food.gram)
async def process_weight_input(message: Message, state: FSMContext):
    data = await state.get_data()
    gram = message.text.strip()

    if not gram.isdigit() or not (0 <= float(gram) <= 8000):
        await message.answer('Пожалуйста, введите корректное кол-во грамм:')
        return

    await state.update_data(gram=gram)
    calories_per_100g = data.get('calories_per_100g')
    total_calories = (int(calories_per_100g) / 100) * float(gram)

    # Сохраняем общее количество калорий для пользователя
    logged_calories = data.get('logged_calories', 0)
    logged_calories += total_calories
    await state.update_data(logged_calories=logged_calories)

    a = await message.answer(
        f'Вы съели: {total_calories:.1f} ккал.\n'
        f'<b>Всего за день:</b> {logged_calories:.1f} ккал.',
        parse_mode='HTML'
    )
    await show_keyboard(a)

async def get_burned_calories(exercise_name):
    url = "https://api.api-ninjas.com/v1/caloriesburned"
    headers = {"X-Api-Key": API_TRAIN}
    params = {"activity": exercise_name}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()  # Получаем ответ как список словарей
        if len(data) == 0:
            return None, None
        else:
            random_index = random.randint(0, len(data) - 1)
            new_data = data[random_index]
            if isinstance(new_data, dict) and len(new_data) > 0:
                return new_data.get('calories_per_hour'), new_data.get('name')
    return None, None


@router.message(Command('training'))
async def start_training(message: Message, state: FSMContext):
    data = await state.get_data()  # Получаем данные состояния
    if not data.get('name'):
        p = await message.answer('<b><u>Вы выбрали кнопку "Тренировка"</u></b>\n\n'
                                 '<b>Ваш профиль пуст.</b> Сначала нужно создать профиль.',
                                 parse_mode='HTML')
        # Возврат в главное меню
        await show_keyboard(p)
    else:
        await message.answer(
            '<b><u>Вы выбрали кнопку "Тренировка"</u></b>\n\n'
            'Напишите, пожалуйста, название тренировки на английском языке.',
            parse_mode='HTML'
        )
        await state.set_state(Workout.name_w)


@router.message(Workout.name_w)
async def training_name(message: Message, state: FSMContext):
    name_w = message.text.strip()
    if not name_w:
        await message.answer("Название тренировки не может быть пустым.")
        return
    elif not re.match('^[A-Za-zs ]+$', name_w):
        await message.answer(
            'Название тренировки должно содержать только буквы на английском языке.')
        return
    await state.update_data(name_w=name_w)
    await message.answer('Как долго длилась Ваше занятие?')
    await state.set_state(Workout.time)


@router.message(Workout.time)
async def training_time(message: Message, state: FSMContext):
    time = message.text.strip()
    if not time.isdigit() or not (0 <= int(time) <= 1440):
        await message.answer('Пожалуйста, введите корректное время (число от 0 до 1440):')
        return
    await state.update_data(time=int(time))

    data = await state.get_data()
    exercise_name = data.get('name_w')
    duration_minutes = data.get('time')

    total_calories, exercise_n = await get_burned_calories(exercise_name)
    burned_calories = data.get('burned_calories', 0)
    if total_calories is not None:
        total_calories_minute = (int(total_calories) // 60) * int(duration_minutes)
        # Сохраняем общее количество калорий для пользователя
        burned_calories += total_calories_minute
        await state.update_data(burned_calories=burned_calories)

        water_intake_w = data.get('water_intake_w', 0)
        water_intake = (int(duration_minutes) // 30) * 200
        water_intake_w += water_intake
        await state.update_data(water_intake_w=water_intake_w)

        a = await message.answer(
            f'🏃‍♀️‍➡️ {exercise_n.capitalize()} {duration_minutes} минут - {total_calories_minute} ккал.\n'
            f'Дополнительно нужно выпить {int(water_intake)} мл воды'
        )
    else:
        a = await message.answer(
            'Не удалось получить данные о сожженных калориях.')
    await show_keyboard(a)

def plot_calorie(message, calorie_goal, logged_calories, burned_calories):
    # Корректируем целевую калорийность с учетом уже заложенных калорий
    adjusted_target = int(logged_calories) - int(burned_calories)

    # Данные для графика
    categories = ['Калории за день', 'Цель калорий']
    values = [adjusted_target, calorie_goal]
    colors = ['orange', 'green']

    # Создаем график
    fig, ax = plt.subplots()
    bars = ax.bar(categories, values, color=colors)

    # Подписи над столбиками
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, yval, round(yval, 2), ha='center', va='bottom')

    # Если есть сожженные калории, рисуем дополнительный красный столбик
    if burned_calories > 0:
        # Добавляем сожженные калории к основному столбику, изменяя его высоту
        ax.bar('Калории за день', int(burned_calories), bottom=int(adjusted_target),
               color='red', label='Сожженные калории')

    # Заголовок и метки
    ax.set_title('Калории за день')
    ax.set_ylabel('Объем (ккал)')

    # Добавляем легенду
    ax.legend(loc='upper left')

    # Сохраняем график во временный файл
    plt.savefig('calorie_day.jpg')
    plt.close()


@router.message(Command('progress'))
async def start_progress(message: Message, state: FSMContext):
    data = await state.get_data()  # Получаем данные состояния
    if not data.get('name'):
        p = await message.answer('<b><u>Вы выбрали кнопку "Прогресс"</u></b>\n\n'
                                 '<b>Ваш профиль пуст.</b> Сначала нужно создать профиль.',
                                 parse_mode='HTML')
        # Возврат в главное меню
        await show_keyboard(p)
    else:
        await message.answer(
            '<b><u>Вы выбрали кнопку "Прогресс"</u></b>\n\n'
            '<b>Ваши результаты за этот день по воде:</b>',
            parse_mode='HTML'
        )
        data = await state.get_data()
        current_temp, total_water_goal, remaining_water = await calculate_water_goal(message, data)
        water_intake_w = data.get('water_intake_w', 0)
        logged_water = data.get('logged_water', 0)
        plot_water_intake(message, logged_water, total_water_goal, water_intake_w)
        if water_intake_w == 0:
            if (int(total_water_goal) - int(logged_water)) == 0:
                await message.answer_photo(photo=FSInputFile('water_intake.jpg', filename='График воды'),
                                           caption=f'Вы выпили {logged_water} мл из необходимых {int(total_water_goal)} мл воды.\n'
                                                   f'<b>Поздравляю!</b> Вы выпили свою дневную норму',
                                           parse_mode='HTML')
            elif (int(total_water_goal) - int(logged_water)) < 0:
                await message.answer_photo(photo=FSInputFile('water_intake.jpg', filename='График воды'),
                                           caption=f'Вы выпили {logged_water} мл из необходимых {int(total_water_goal)} мл воды.\n'
                                                   f'<b>Осторожно!</b> Вы выпили больше нормы',
                                           parse_mode='HTML')
            else:
                await message.answer_photo(photo=FSInputFile('water_intake.jpg', filename='График воды'),
                                           caption=f'Вы выпили {logged_water} мл из необходимых {int(total_water_goal)} мл воды.\n'
                                                   f'Осталось еще {int(remaining_water)} мл до выполнения нормы.')
        else:
            if (int(total_water_goal) + int(water_intake_w) - int(logged_water)) == 0:
                await message.answer_photo(photo=FSInputFile('water_intake.jpg', filename='График воды'),
                                           caption='<b>Хорошая тренировка!</b>\n'
                                                   f'Вы выпили {logged_water} мл из необходимых {int(total_water_goal) + int(water_intake_w)} мл воды.\n'
                                                   f'<b>Поздравляю!</b> Вы выпили свою дневную норму',
                                           parse_mode='HTML')
            elif (int(total_water_goal) + int(water_intake_w) - int(logged_water)) < 0:
                await message.answer_photo(photo=FSInputFile('water_intake.jpg', filename='График воды'),
                                           caption='<b>Хорошая тренировка!</b>\n'
                                                   f'Вы выпили {logged_water} мл из необходимых {int(total_water_goal) + int(water_intake_w)} мл воды.\n'
                                                   f'<b>Осторожно!</b> Вы выпили больше нормы',
                                           parse_mode='HTML')
            else:
                await message.answer_photo(photo=FSInputFile('water_intake.jpg', filename='График воды'),
                                           caption='<b>Хорошая тренировка!</b>\n'
                                                   f'Вы выпили {logged_water} мл из необходимых {int(total_water_goal) + int(water_intake_w)} мл воды.\n'
                                                   f'Осталось еще {int(total_water_goal) + int(water_intake_w) - int(logged_water)} мл до выполнения нормы.',
                                           parse_mode='HTML')

        await message.answer('<b>Ваши результаты за этот день:</b>',
                             parse_mode='HTML')
        calorie_goal = data.get('custom_calorie_goal', 0)
        logged_calories = data.get('logged_calories', 0)
        burned_calories = data.get('burned_calories', 0)
        plot_calorie(message, calorie_goal, logged_calories, burned_calories)
        a = await message.answer_photo(photo=FSInputFile('calorie_day.jpg', filename='График калорий'),
                                       caption=f'Съедено  {int(logged_calories)} калл из {float(calorie_goal)} калл.\n'
                                               f'Согнали {int(burned_calories)} калл.\n'
                                               f'Нормализация {int(logged_calories) - int(burned_calories)} калл.',
                                       parse_mode='HTML')
        await show_keyboard(a)


