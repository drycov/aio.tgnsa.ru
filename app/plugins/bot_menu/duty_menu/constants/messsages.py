from enum import Enum

from ..constants.menu_label import DutySymbols





class DutyMessages(Enum):
    # Главное меню
    MENU_MAIN = f"{DutySymbols.DUTY.value} Главное меню дежурств"
    VIEW_SCHEDULE = f"{DutySymbols.DUTY.value} Ваши ближайшие дежурства:"
    VIEW_TEAM = f"{DutySymbols.TEAM.value} Состав вашей дежурной команды:"
    NO_DUTY = f"{DutySymbols.FAIL.value} У вас нет назначенных дежурств."
    
    # Обмен сменами
    REQUEST_SWAP = f"{DutySymbols.SWAP.value} Укажите смену, которую хотите обменять."
    CONFIRM_SWAP = f"{DutySymbols.SWAP.value} Обмен подтверждён."
    DENY_SWAP = f"{DutySymbols.FAIL.value} Обмен отклонён."
    SWAP_PENDING = f"{DutySymbols.INFO.value} Запрос обмена отправлен, ожидайте подтверждения."

    # Инциденты
    REPORT_INCIDENT = f"{DutySymbols.INCIDENT.value} Опишите проблему для создания инцидента."
    INCIDENT_REPORTED = f"{DutySymbols.SUCCESS.value} Инцидент зарегистрирован."
    INCIDENT_CLOSED = f"{DutySymbols.SUCCESS.value} Инцидент закрыт."
    INCIDENT_FAIL = f"{DutySymbols.FAIL.value} Ошибка при работе с инцидентом."

    # Ошибки
    ERROR_UNAUTHORIZED = f"{DutySymbols.FAIL.value} У вас нет доступа к расписанию."
    ERROR_UNKNOWN = f"{DutySymbols.FAIL.value} Произошла ошибка. Повторите попытку позже."
