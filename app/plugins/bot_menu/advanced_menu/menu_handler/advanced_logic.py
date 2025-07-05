import asyncio
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from pythonping import ping

from app.core.logging_setup import configure_logger
from app.core.utils.network_utils import NetworkUtils
from ..constants.states import Advanced
from app.bot.keyboards.base import in_back_keyboard
from app.bot.fsm.state_manager import StateManager

logger = configure_logger().bind(component=f"{__name__}")

async def handle_cidr_logic(message: Message, state: FSMContext):
    """Обработчик CIDR калькулятора с расширенной информацией"""
    subnet = message.text.strip()
    net, error = await NetworkUtils.validate_subnet(subnet)

    if error:
        await message.answer(error, reply_markup=in_back_keyboard, parse_mode="HTML")
        await state.update_data(waiting_for_subnet=False)
        return

    try:
        info = await NetworkUtils.get_network_info(net)

        result = (
            f"Сеть:        {info['network']}\n"
            f"Маска:       {info['netmask']}\n"
            f"Broadcast:   {info['broadcast']}\n"
            f"Диапазон:    {info['first_host']} - {info['last_host']}\n"
            f"Хостов:      {info['total_hosts']}\n"
            f"Wildcard:    {info['hostmask']}\n"
            f"Префикс:     /{info['prefixlen']}\n"
            f"Тип:         {'Private' if info['is_private'] else 'Public'}"
        )

        text = f"<b>🔢 Подробный расчёт для <code>{subnet}</code></b>\n\n<pre>{result}</pre>"

    except Exception as e:
        text = f"⚠️ <b>Ошибка обработки</b>\n{e}"
        logger.error(f"CIDR error: {e}")

    display_data = {
        "text": text,
        "reply_markup": in_back_keyboard,
        "parse_mode": "HTML",
    }

    await StateManager.set_state_with_history(state, Advanced.MENU, display_data)
    await message.answer(**display_data)  # ✅ именно так
    await state.update_data(waiting_for_subnet=False)


async def handle_p2p_logic(message: Message, state: FSMContext):
    """Обработчик P2P калькулятора с проверкой подсети"""
    subnet = message.text.strip()
    net, error = await NetworkUtils.validate_subnet(subnet)

    if error:
        await message.answer(error, reply_markup=in_back_keyboard, parse_mode="HTML")
        await state.update_data(waiting_for_subnet=False)
        return

    try:
        if net.prefixlen > 30:
            raise ValueError("Минимальный размер подсети для P2P - /30")

        hosts = list(net.hosts())
        if len(hosts) < 2:
            raise ValueError("Недостаточно адресов для P2P связи")

        result = (
            f"Устройство A:\n"
            f"IP:        {hosts[0]}\n"
            f"Маска:     {net.netmask}\n"
            f"Шлюз:      {hosts[1]}\n\n"
            f"Устройство B:\n"
            f"IP:        {hosts[1]}\n"
            f"Маска:     {net.netmask}\n"
            f"Шлюз:      {hosts[0]}\n\n"
            f"Доступные адреса: {len(hosts)}"
        )

        text = f"<b>🔗 P2P конфигурация для <code>{subnet}</code></b>\n\n<pre>{result}</pre>"

    except ValueError as e:
        text = f"❌ <b>Ошибка</b>\n{e}\n\nПример: 192.168.1.0/30"
    except Exception as e:
        text = f"⚠️ <b>Неожиданная ошибка</b>\n{e}"
        logger.error(f"P2P error: {e}")

    display_data = {
        "text": text,
        "reply_markup": in_back_keyboard,
        "parse_mode": "HTML",
    }

    await StateManager.set_state_with_history(state, Advanced.MENU, display_data)
    await message.answer(**display_data)  # ✅ именно так
    await state.update_data(waiting_for_subnet=False)


async def handle_ping_logic(message: Message, state: FSMContext):
    """Обработчик ping с расширенной статистикой"""
    host = message.text.strip()
    progress_msg = await message.answer("🔄 Выполняю ping...")

    try:
        # Выполняем ping асинхронно
        response = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None, lambda: ping(host, count=4, timeout=2, verbose=False)
            ),
            timeout=10,
        )

        if response.success():
            successful = [r for r in response if r.success]
            details = [
                f"{i + 1}) Ответ: {r.time_elapsed * 1000:.2f} мс"
                for i, r in enumerate(successful)
            ]

            stats = (
                f"📊 Статистика:\n"
                f"• Отправлено: {len(response)}\n"
                f"• Потеряно: {len(response) - len(successful)}\n"
                f"• Среднее: {sum(r.time_elapsed for r in successful) / len(successful) * 1000:.2f} мс"
            )

            text = f"✅ <b>Ping {host}</b>\n<pre>{chr(10).join(details)}</pre>\n{stats}"
        else:
            text = f"❌ <b>{host} недоступен</b>\nПроверьте адрес и доступность"

    except asyncio.TimeoutError:
        text = "🕒 Превышено время ожидания ping"
    except Exception as e:
        text = f"⚠️ <b>Ошибка</b>\n{str(e)}"
        logger.error(f"Ping error: {e}")
    finally:
        await progress_msg.delete()

    display_data = {
        "text": text,
        "reply_markup": in_back_keyboard,
        "parse_mode": "HTML",
    }

    await StateManager.set_state_with_history(state, Advanced.MENU, display_data)
    await message.answer(**display_data)
    await state.update_data(waiting_for_host=False)
