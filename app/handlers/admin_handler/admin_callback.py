from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ReplyKeyboardRemove, FSInputFile
from tabulate import tabulate

from app.bot_instance import bot
from app.constants import Messages
from app.constants.states import MainCommands, RegistrationForm
from app.keyboards import on_enter_keyboard
from app.models import User
from app.utils import StateManager, HelperFunctions
from app.utils.logger_instance import app_logger
from config import Config
from healthy import Healthy
from logging_config import LoggingConfig

router = Router()
health_checker = Healthy()


@router.callback_query(lambda c: c.data == "approve_user")
async def approve_user(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("Ваши данные подтверждены!")
    app_logger.info(f"Пользователь {callback_query.from_user.id} подтвердил свои данные.")

    # Сбор данных пользователя из состояния
    user_data = await state.get_data()
    verification_code = User.generate_verification_code()
    user_hash = User.generate_hash(verification_code)
    app_logger.info(f"Код подтверждения: {verification_code}")

    try:
        # Создаем новый объект User
        new_user = User(
            is_bot=callback_query.from_user.is_bot,
            tg_id=callback_query.from_user.id,
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            company_post=user_data['company_post'],
            phone_number=user_data['phone_number'],
            username=callback_query.from_user.username or f"u{callback_query.from_user.id}",
            is_admin=False,
            is_allowed=False,
            is_verified=False,
            verification_code=verification_code,
            email=user_data['email'],
            hash=user_hash
        )

        # Данные для таблицы
        table_data = [
            ["Telegram ID", new_user.tg_id],
            ["Username", new_user.username],
            ["Полное имя", f"{new_user.first_name} {new_user.last_name}"],
            ["Должность", new_user.company_post],
            ["Phone", new_user.phone_number],
            ["E-Mail", new_user.email],
            ["Подтвердить", f"/approve_{callback_query.from_user.id}"],
            ["Отклонить", f"/reject_{callback_query.from_user.id}"]
        ]

        # Создание таблицы из данных
        table_str = tabulate(table_data, tablefmt="plain")
        admin_message = f"Новый пользователь ожидает подтверждения:\n\n{table_str}"

        # Сохранение пользователя в базу данных
        User.create(new_user.model_dump())
        await callback_query.message.answer(Messages.USER_SAVED_IN_DB.value, reply_markup=on_enter_keyboard,
                                            parse_mode="HTML")

        # Проверка наличия admin ID
        admin_id = Config.DEFAULT_ADMIN_ID
        if admin_id is None:
            app_logger.error("DEFAULT_ADMIN_ID не задан в конфигурации.")
            await callback_query.answer(Messages.ERROR_GENERAL.value, parse_mode="HTML")
            return

        # Отправка таблицы с данными пользователя администратору
        try:
            await bot.send_message(admin_id, admin_message, parse_mode="HTML")
        except Exception as send_error:
            app_logger.error(f"Ошибка при отправке сообщения администратору (chat_id={admin_id}): {send_error}")

    except Exception as e:
        app_logger.error(f"Ошибка при создании пользователя с tg_id {callback_query.from_user.id}: {e}")
        await callback_query.answer(Messages.ERROR_GENERAL.value, parse_mode="HTML")

    # Очищаем состояние после завершения регистрации
    await state.clear()
    await state.set_state(MainCommands.START)


@router.callback_query(lambda c: c.data == "reject_user")
async def reject_user(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("Пожалуйста, повторите ввод данных.")
    app_logger.info(f"Пользователь {callback_query.from_user.id} отклонил свои данные.")
    await callback_query.message.edit_text("Ваши данные отклонены. Пожалуйста, начните регистрацию заново.")

    await StateManager.set_state_with_previous(state, RegistrationForm.first_name)
    await bot.send_message(callback_query.from_user.id, Messages.REGISTER_FIRST_NAME.value,
                           reply_markup=ReplyKeyboardRemove())


@router.callback_query(lambda c: c.data == "check_components")
async def check_components(callback_query: CallbackQuery):
    """
    Проверка состояния всех компонентов.
    """
    await bot.answer_callback_query(callback_query.id)
    statuses = await health_checker.get_all_statuses()
    response = "\n".join([f"{name}: {status}" for name, status in statuses.items()])
    await bot.send_message(callback_query.from_user.id, f"Статусы компонентов:\n{response}")


@router.callback_query(lambda c: c.data == "reload_checks")
async def reload_checks(callback_query: CallbackQuery):
    """
    Перезагрузка проверок здоровья.
    """
    await bot.answer_callback_query(callback_query.id)
    await health_checker.perform_health_checks()
    await bot.send_message(callback_query.from_user.id, "Проверки здоровья успешно перезагружены!")


@router.callback_query(lambda c: c.data == "get_logs")
async def get_logs(callback_query: CallbackQuery):
    """
    Получение логов.
    """
    await bot.answer_callback_query(callback_query.id)
    # Пример получения логов (здесь можно настроить свои пути к лог-файлам)
    log_path = LoggingConfig.LOG_DIR / LoggingConfig.LOG_FILE
    try:
        # Используем InputFile для отправки файла
        # Используем FSInputFile для отправки файла
        log_file = FSInputFile(log_path)
        await bot.send_document(callback_query.from_user.id, document=log_file)
    except FileNotFoundError:
        await bot.send_message(callback_query.from_user.id, "Файл логов не найден.")
    except Exception as e:
        HelperFunctions.log_error(action=f"{__name__}.get_logs", error=e)
        await bot.send_message(callback_query.from_user.id, f"Произошла ошибка: {str(e)}")


@router.callback_query(lambda c: c.data == "get_health")
async def send_system_health(callback_query: CallbackQuery):
    """
    Отправляет здоровье системы в Telegram.
    """
    # Выполняем проверки здоровья
    await health_checker.perform_health_checks()
    system_health = health_checker.calculate_system_health()

    # Заменяем статусы на иконки
    status_icons = {
        "OK": "✅",
        "FAILED": "❌",
        "ERROR": "⚠️",
        "N/A": "❔",
    }

    await bot.answer_callback_query(callback_query.id)

    # Формируем сообщение
    report = f"<b>Общее состояние системы:</b> {status_icons[system_health['system_status']]}\n\n"

    if system_health["failed_components"]:
        report += "<b>Неуспешные компоненты:</b>\n"
        report += "\n".join(f"  - {component}" for component in system_health["failed_components"])
        report += "\n\n"

    if system_health["error_components"]:
        report += "<b>Ошибки компонентов:</b>\n"
        report += "\n".join(f"  - {component}" for component in system_health["error_components"])
        report += "\n\n"

    report += "<b>Детали:</b><pre>\n"
    for name, details in system_health["details"].items():
        status_icon = status_icons.get(details["status"], "❔")
        report += (
            f"<b>{name}</b>:\n"
            f"  - Статус: {status_icon}\n"
            f"  - Детали: {details['details']}\n"
        )
    report += "</pre>\n"

    # Отправляем отчет в виде сообщения
    await bot.send_message(callback_query.from_user.id, report, parse_mode="HTML")
