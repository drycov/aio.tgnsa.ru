from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from bot.constants import MenuLabels


def generate_main_keyboard(is_admin: bool=False) -> ReplyKeyboardMarkup:
    """
    Создает основную клавиатуру с учетом статуса is_admin.
    Если пользователь админ, добавляются дополнительные кнопки.
    """
    keyboard = [
        [
            KeyboardButton(text=MenuLabels.DEVICE_CHECK.value),
            KeyboardButton(text=MenuLabels.ADVANCED.value),
        ], [KeyboardButton(text=MenuLabels.ERTM_MENU.value)],

        [KeyboardButton(text=MenuLabels.TASK_MANAGER.value),
         KeyboardButton(text=MenuLabels.USER_PROFILE.value),
         ],
        [KeyboardButton(text=MenuLabels.EXIT.value)],
    ]

    if is_admin:
        keyboard.insert(1, [KeyboardButton(text=MenuLabels.ADMIN_PANEL.value)])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def admin_menu() -> ReplyKeyboardMarkup:
    """Создаем клавиатуру для админов"""
    keyboard = [
        [
            KeyboardButton(text=MenuLabels.VIEW_USERS.value),
            KeyboardButton(text=MenuLabels.SEND_BROADCAST.value),
        ],
        [KeyboardButton(text="Статус системы")],
        [KeyboardButton(text=MenuLabels.BACK.value)],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def system_info_menu() -> ReplyKeyboardMarkup:
    """Создает клавиатуру для информации о системе."""
    keyboard = [
[KeyboardButton(text="📊 Состояние системы")],
        [
            KeyboardButton(text="🔍 Проверить компоненты"),
            KeyboardButton(text="🔄 Перезагрузить проверки"),
        ],
        [KeyboardButton(text="📜 Получить логи")],
        [KeyboardButton(text=MenuLabels.BACK.value)],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


# Клавиатура подтверждения действий
confirm_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=MenuLabels.USER_APPROVE.value), KeyboardButton(text=MenuLabels.USER_REJECT.value)]
    ],
    resize_keyboard=True
)

# Инлайн-клавиатура подтверждения
confirm_keyboard_inl = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text=MenuLabels.USER_APPROVE.value, callback_data="approve_user"),
        InlineKeyboardButton(text=MenuLabels.USER_REJECT.value, callback_data="reject_user")
    ]
])


# Кнопки для выбора поля редактирования
def generate_edit_choice_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Имя", callback_data="edit_first_name")],
        [InlineKeyboardButton(text="Фамилия", callback_data="edit_last_name")],
        [InlineKeyboardButton(text="Должность", callback_data="edit_company_post")],
        [InlineKeyboardButton(text="Телефон", callback_data="edit_phone_number")],
        [InlineKeyboardButton(text="Email", callback_data="edit_email")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="profile_back")]
    ])
