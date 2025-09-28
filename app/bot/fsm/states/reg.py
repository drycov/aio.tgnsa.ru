from aiogram.fsm.state import State, StatesGroup


# Форма регистрации пользователя
class RegistrationForm(StatesGroup):
    first_name = State()
    last_name = State()
    deportament = State()
    company_post = State()
    phone_number = State()
    email = State()
    confirmation = State()
