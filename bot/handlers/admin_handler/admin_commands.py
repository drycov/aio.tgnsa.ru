import re
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.types.input_file import FSInputFile

from bot.bot_instance import bot
from bot.constants import Messages, MenuLabels
from bot.constants.states import MainCommands
from bot.keyboards import admin_menu, system_info_menu
from bot.models import User
from bot.utils import StateManager, HelperFunctions
from healthy import Healthy
from logging_config import LoggingConfig

router = Router()
health_checker = Healthy()
current_date = HelperFunctions.get_current_date()

# Регулярное выражение для проверки формата команды
COMMAND_PATTERN = re.compile(r"^/(approve|reject)_(\d+)$")

# Статусы для иконок
STATUS_ICONS = {
    "OK": "✅",
    "FAILED": "❌",
    "ERROR": "⚠️",
    "N/A": "❔",
}


def format_system_health(system_health, current_date=current_date,detailed=False):
    """Формирует текстовый отчет о состоянии системы."""
    # Общий статус системы
    report = f"<b>Общее состояние системы:</b> {STATUS_ICONS.get(system_health['system_status'], '❔')}\n\n"

    # Неуспешные компоненты
    if system_health["failed_components"]:
        report += "<b>Неуспешные компоненты:</b>\n" + "\n".join(
            f"  - {component}" for component in system_health["failed_components"]
        ) + "\n"

    # Компоненты с ошибками
    if system_health["error_components"]:
        report += "<b>Ошибки компонентов:</b>\n" + "\n".join(
            f"  - {component}" for component in system_health["error_components"]
        ) + "\n"
    if detailed:
        # Детальная информация о каждом компоненте
        report += "<b>Детали:</b>\n<pre>"
        for title, details in system_health["details"].items():
            status_icon = STATUS_ICONS.get(details["status"], "❔")
            inform = f" ({details['inform']})" if details.get("inform", "N/A") != "N/A" else ""
            report += (
                f"{details['title']} {status_icon}:"
                # f"  - Статус: \n"
                f"{details['details']}{inform}\n"
            )
        report += "</pre>"

    # Добавление времени выполнения
    report += f"\n<i>Выполнено:  {current_date}</i>"

    return report

@router.message(F.text == MenuLabels.ADMIN_PANEL.value)
async def admin_panel_command(message: Message, state: FSMContext):
    """Отображение панели администратора."""
    keyboard = admin_menu()
    display_data = {"text": "Администрирование.", "reply_markup": keyboard}
    await StateManager.set_state_with_previous(state, MainCommands.ADMIN_PANEL, display_data)
    await message.answer(**display_data)


@router.message(F.text == "Статус системы")
async def system_panel_command(message: Message, state: FSMContext):
    """Отображение меню статуса системы."""
    keyboard = system_info_menu()
    await health_checker.perform_health_checks()
    system_health = health_checker.calculate_system_health()

    report = format_system_health(system_health)
    # report += f"\n<i>Выполнено:  <code>{current_date}</code></i>"

    await StateManager.set_state_with_previous(state, MainCommands.SYSTEM_MENU, {"text": report})
    await message.answer(report, reply_markup=keyboard, parse_mode="HTML")


@router.message(F.text == "📊 Состояние системы")
async def send_system_health(message: Message):
    """Отправляет состояние системы."""
    await health_checker.perform_health_checks()
    system_health = health_checker.calculate_system_health()
    report = format_system_health(system_health, current_date,detailed=True)
    # report += f"\n<i>Выполнено:  <code>{current_date}</code></i>"
    await message.answer(report, parse_mode="HTML")


@router.message(F.text == "🔍 Проверить компоненты")
async def check_components(message: Message):
    """Проверка состояния всех компонентов."""
    statuses = await health_checker.get_all_statuses()
    response = "\n".join([f"{name}: {status}" for name, status in statuses.items()])
    response += f"\n<i>Выполнено:  <code>{current_date}</code></i>"
    await message.answer(f"<b>Статусы компонентов:</b>\n\n{response}", parse_mode="HTML")


@router.message(F.text == "🔄 Перезагрузить проверки")
async def reload_checks(message: Message):
    """Перезагрузка проверок здоровья."""
    await health_checker.perform_health_checks()
    response = f"<b>Проверки здоровья успешно перезагружены.</b>\n<i>Выполнено:  <code>{current_date}</code></i>"
    await message.answer(response, parse_mode="HTML")


@router.message(F.text == "📜 Получить логи")
async def get_logs(message: Message):
    """Получение логов."""
    log_path = LoggingConfig.LOG_DIR / LoggingConfig.LOG_FILE
    try:
        log_file = FSInputFile(log_path)
        await message.answer_document(document=log_file)
    except FileNotFoundError:
        await message.answer("Файл логов не найден.")
    except Exception as e:
        HelperFunctions.log_error(action=f"{__name__}.get_logs", error=e)
        await message.answer(f"Произошла ошибка: {str(e)}")


@router.message(lambda message: message.text and COMMAND_PATTERN.match(message.text))
async def admin_approval(message: Message):
    """Обработка команд одобрения или отклонения пользователя."""
    match = COMMAND_PATTERN.match(message.text)
    if not match:
        await message.answer("Некорректный формат команды.")
        return

    action, user_id = match.groups()
    user_id = int(user_id)

    user = User.get_by_tg_id(user_id)
    if not user:
        await message.answer(f"Пользователь с ID {user_id} не найден.")
        return

    if action == "approve":
        user.update({"is_verified": True, "is_allowed": True})
        await bot.send_message(user_id, Messages.USER_ALLOWED_IN_DB.value)
        await message.answer(Messages.USER_ADDED.value)
    elif action == "reject":
        User.delete(user_id)
        await bot.send_message(user_id, Messages.USER_REJECTED_FROM_DB.value)
        await message.answer(Messages.USER_REJECTED.value)
