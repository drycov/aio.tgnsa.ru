from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from typing import Union, List, Tuple

from app.bot.constants.labels import MenuLabels
from app.bot.constants.positions import POSITIONS_BY_DEPARTMENT
from app.core.config import logger


def build_auth_keyboard(is_authenticated: bool) -> ReplyKeyboardMarkup:
    """
    Builds an authentication keyboard.

    :param is_authenticated: Whether the user is authenticated.
    :return: ReplyKeyboardMarkup
    """
    logger.debug(f"Build keyboard: {'ENTER' if not is_authenticated else 'EXIT'}")

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=(
                        MenuLabels.ENTER.value
                        if not is_authenticated
                        else MenuLabels.EXIT.value
                    )
                )
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Действие",
    )


on_enter_keyboard = build_auth_keyboard(False)

# Keyboard for sending contact
send_contact_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=MenuLabels.SHARE_CONTACT.value, request_contact=True)],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,  # Keeps the keyboard visible
)
send_contact_keyboard.input_field_placeholder = MenuLabels.SHARE_CONTACT.value

# Confirmation keyboard
send_confirm_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")],
    ],
)


def generate_confirm_keyboard(
    action: str,
    payload: Union[int, str],
    confirm_label: str = "✅ Подтвердить",
    cancel_label: str = "❌ Отклонить",
    confirm_suffix: str = "confirm",
    cancel_suffix: str = "cancel",
) -> InlineKeyboardMarkup:
    """
    Generates a universal confirmation keyboard.

    :param action: Prefix action, e.g., 'registration', 'admin', 'delete_user'
    :param payload: Additional data (user_id, object, etc.)
    :param confirm_label: Text for the confirmation button
    :param cancel_label: Text for the cancellation button
    :param confirm_suffix: Suffix for the confirmation action
    :param cancel_suffix: Suffix for the cancellation action
    :return: InlineKeyboardMarkup
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=confirm_label,
                    callback_data=f"{action}:{confirm_suffix}:{payload}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=cancel_label,
                    callback_data=f"{action}:{cancel_suffix}:{payload}",
                )
            ],
        ]
    )


def generate_department_keyboard() -> InlineKeyboardMarkup:
    """
    Generates a department selection keyboard.

    :return: InlineKeyboardMarkup
    """
    logger.debug("Generating department selection keyboard")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"department:{name}")]
            for name in POSITIONS_BY_DEPARTMENT.keys()
        ]
    )


def generate_position_keyboard(department: str) -> InlineKeyboardMarkup:
    """
    Generates a position selection keyboard for a given department.

    :param department: Department name
    :return: InlineKeyboardMarkup
    """
    department = department.upper()
    positions = POSITIONS_BY_DEPARTMENT.get(department)

    if not positions:
        logger.warning(f"Department not found: {department}")
        # Fallback: back button on error
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ Неверное направление",
                        callback_data="back_to_departments",
                    )
                ]
            ]
        )

    logger.debug(f"Generating position selection keyboard for department: {department}")
    keyboard_buttons = [
        [InlineKeyboardButton(text=title, callback_data=f"position:{code}")]
        for title, code in positions
    ]

    # Add back button
    keyboard_buttons.append(
        [InlineKeyboardButton(text="⬅ Назад", callback_data="back_to_departments")]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


# Pre-generated department keyboard
in_department_keyboard = generate_department_keyboard()

# Inline back button
in_back_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=MenuLabels.BACK.value, callback_data="back")]
    ]
)
