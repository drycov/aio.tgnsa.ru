# error_handler.py (и любые другие файлы)
from bot.utils.logger import get_app_logger

app_logger = get_app_logger()
app_logger.info("This message includes the module name automatically.")
