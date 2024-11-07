# Пример шагов формы регистрации
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message

from app.keyboards import in_back_keyboard
from app.utils import StateManager


class Registration(StatesGroup):
    STEP_1 = State()
    STEP_2 = State()
    STEP_3 = State()


router = Router()


@router.message(F.text == '/test1')
async def start_registration(message: Message, state: FSMContext):
    await StateManager.set_state_with_previous(state, Registration.STEP_1.state)
    await message.answer("Начало регистрации. Шаг 1.")


@router.message(F.text == '/test2')  # условие перехода на шаг 2
async def registration_step_2(message: Message, state: FSMContext):
    await StateManager.set_state_with_previous(state, Registration.STEP_2.state)
    await message.answer("Шаг 2 регистрации.",reply_markup=in_back_keyboard)
