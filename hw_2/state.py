from aiogram.fsm.state import State, StatesGroup

class User(StatesGroup):
    name = State()  # Состояние для имени
    weight = State()  # Состояние для веса
    height = State()  # Состояние для роста
    age = State()  # Состояние для возраста
    activity_level = State()  # Состояние для уровня активности
    city = State()  # Состояние для города
    calorie_goal = State()  # Состояние для цели калорий
    logged_water = State() # Состояние для выпитой воды
    logged_calories = State() # Состояние для полученных калорий
    burned_calories = State() # Состояние для сожженных калорий

class Food(StatesGroup):
    product = State() # Состояние для названия продукта
    gram = State() # Состояние для съеденных грамм продукта

class Workout(StatesGroup):
    name_w = State() # Состояние для названия тренировки
    time = State() # Состояние для времени тренировки
    water_intake_w = State() # Состояние для дополнительной воды