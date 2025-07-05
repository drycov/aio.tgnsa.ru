from enum import Enum


class Symbols(Enum):
    TECH_NETWORK = "🌐"
    TECH_P2P = "🔗"
    EMOJI_DEVICE = "💻"
    ROLE_CLI = "📟"  # Командная строка (CLI)
    EMOJI_TOOLS = "🧰"  # Инструменты


class MenuLabels(Enum):
    ADVANCED = f"{Symbols.EMOJI_TOOLS.value} Дополнительно"
    CIDR_CALC = f"{Symbols.TECH_NETWORK.value} Расчет сети"
    P2P_CALC = f"{Symbols.TECH_P2P.value} Рассчитать P2P-пару"
    SUBNET_CALC = f"{Symbols.EMOJI_DEVICE.value} Калькулятор подсети"
    PING_DEVICE = f"{Symbols.ROLE_CLI.value} Ping"
    TRACEROUTE = f"Трасировка"
