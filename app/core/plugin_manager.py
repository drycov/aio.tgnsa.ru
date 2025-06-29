import importlib
import logging
from asyncio import Lock
from pathlib import Path
import tomllib
from typing import Optional
from enum import Enum, auto
import inspect
from collections import defaultdict, deque

from app.core.patchs import APP_DIR, BASE_DIR

logger = logging.getLogger(__name__)  # Можно заменить на кастомный LoggerManager
DEFAULT_PLUGIN_DIR = APP_DIR / "plugins"
DEFAULT_CONFIG_PATHS = [
    APP_DIR / "plugins.toml",
    BASE_DIR / "config" / "plugins.toml",
    Path.home() / ".config" / "tgnms" / "plugins.toml",
]


class PluginState(Enum):
    CREATED = auto()
    LOADED = auto()
    INITIALIZED = auto()


class PluginManager:
    _instance: Optional["PluginManager"] = None
    _initialized = False
    _lock = Lock()

    def __init__(
        self,
        plugin_dir: Optional[Path] = None,
        plugin_config_file: Optional[Path] = None,
    ):
        self._state = PluginState.CREATED
        self.plugin_dir = plugin_dir or DEFAULT_PLUGIN_DIR
        self.plugin_config_file = self._resolve_config_path(plugin_config_file)

        if not self.plugin_dir.exists() or not self.plugin_dir.is_dir():
            logger.warning(
                "📁 Папка плагинов %s не существует, будет создана", self.plugin_dir
            )
            self.plugin_dir.mkdir(parents=True, exist_ok=True)

        self.plugins = {}
        self.plugin_groups: dict[str, list[str]] = defaultdict(list)
        self.plugin_config = self._load_plugin_config(self.plugin_config_file)
        logger.debug(
            "🔧 PluginManager инициализирован с plugin_dir=%s, config=%s",
            self.plugin_dir,
            self.plugin_config_file,
        )

    def _resolve_config_path(self, user_path: Optional[Path]) -> Path:
        if user_path and user_path.exists():
            return user_path
        for candidate in DEFAULT_CONFIG_PATHS:
            if candidate.exists():
                return candidate
        logger.warning("⚠️ Ни один из путей конфигурации не найден — fallback к первому")
        return DEFAULT_CONFIG_PATHS[0]

    def _load_plugin_config(self, config_path: Path) -> dict:
        if config_path.exists():
            try:
                with config_path.open("rb") as f:
                    config = tomllib.load(f)
                logger.info("📄 Конфигурация плагинов загружена из %s", config_path)
                return config
            except Exception as e:
                logger.error("❌ Ошибка чтения конфигурации TOML: %s", e)
        else:
            logger.debug(
                "📜 Конфигурационный файл отсутствует, будет использоваться пустой словарь"
            )

        return {}

    def _is_plugin_enabled(self, plugin_name: str) -> bool:
        plugin_entry = self.plugin_config.get("plugins", {}).get(plugin_name, {})
        return plugin_entry.get("enabled", True)

    def _resolve_dependencies(self) -> list[str]:
        graph = defaultdict(list)
        indegree = defaultdict(int)

        for plugin, meta in self.plugin_config.get("plugins", {}).items():
            deps = meta.get("depends_on", [])
            for dep in deps:
                graph[dep].append(plugin)
                indegree[plugin] += 1
                indegree.setdefault(dep, 0)

        queue = deque([n for n in indegree if indegree[n] == 0])
        sorted_plugins = []

        while queue:
            node = queue.popleft()
            sorted_plugins.append(node)
            for neighbor in graph[node]:
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_plugins) != len(indegree):
            raise RuntimeError("❌ Обнаружены циклические зависимости в DAG")

        return sorted_plugins

    @staticmethod
    def get_instance() -> Optional["PluginManager"]:
        return PluginManager._instance

    @staticmethod
    def create_once(
        plugin_dir: Optional[Path] = APP_DIR / "plugins",
        plugin_config_file: Optional[Path] = BASE_DIR / "config" / "plugins.toml",
    ) -> "PluginManager":
        if PluginManager._instance is None:
            logger.info("🆕 Создание singleton PluginManager")
            PluginManager._instance = PluginManager(plugin_dir, plugin_config_file)
        else:
            logger.debug(
                "🔁 PluginManager уже создан — возвращаем существующий инстанс"
            )
        return PluginManager._instance

    @classmethod
    def is_initialized(cls) -> bool:
        return cls._initialized

    @classmethod
    async def ensure_initialized(
        cls, settings: Optional[dict] = None
    ) -> "PluginManager":
        async with cls._lock:
            if cls._instance is None:
                logger.error("❌ Попытка инициализации без вызова create_once()")
                raise RuntimeError(
                    "PluginManager не создан. Вызовите create_once() сначала."
                )

            if cls._instance._state == PluginState.CREATED:
                logger.info("🚀 Инициализация PluginManager начата")
                await cls._instance.load_all(settings=settings)
                cls._instance._state = PluginState.LOADED
                await cls._instance.init_all(settings=settings)
                cls._instance._state = PluginState.INITIALIZED
                cls._initialized = True
                logger.info("✅ PluginManager успешно инициализирован")
            else:
                logger.debug(
                    "⏭ PluginManager уже инициализирован — состояние: %s",
                    cls._instance._state.name,
                )

            return cls._instance

    @classmethod
    async def reload_all(cls, settings: Optional[dict] = None):
        async with cls._lock:
            if cls._instance is None:
                raise RuntimeError("PluginManager не создан.")
            logger.info("♻️ Перезагрузка всех плагинов")
            await cls._instance.load_all(settings=settings)
            await cls._instance.init_all(settings=settings)
            cls._instance._state = PluginState.INITIALIZED
            cls._initialized = True

    async def load_all(self, settings: Optional[dict] = None):
        logger.info("📦 Загрузка плагинов из директории: %s", self.plugin_dir)
        plugin_dirs = sorted(self.plugin_dir.rglob("__init__.py"))
        logger.debug("🔍 Найдено %d потенциальных плагинов", len(plugin_dirs))

        for init_file in plugin_dirs:
            plugin_path = init_file.parent
            plugin_name = plugin_path.name

            try:
                rel_path = plugin_path.relative_to(APP_DIR.parent)
                dotted_path = ".".join(rel_path.parts)
                mod = importlib.import_module(dotted_path)
                plugin = getattr(mod, "plugin", None)
                if plugin:
                    if not self._is_plugin_enabled(plugin_name):
                        logger.info("⏹ Пропускаем отключённый плагин: %s", plugin_name)
                        continue
                    self.plugins[plugin_name] = plugin

                    # Группировка
                    group = self.plugin_config.get("plugins", {}).get(plugin_name, {}).get("group")
                    if group:
                        self.plugin_groups[group].append(plugin_name)

                    logger.info("✅ Загружен плагин: %s", plugin_name)
                else:
                    logger.warning("⚠️ Плагин %s не содержит 'plugin'", plugin_name)
            except Exception as e:
                logger.exception("❌ Ошибка загрузки плагина %s: %s", plugin_name, e)

    async def init_all(self, settings: Optional[dict] = None):
        logger.info("🧹 Инициализация %d плагинов", len(self.plugins))

        for name, plugin in self.plugins.items():
            logger.info("🔄 Инициализируем плагин: %s", name)

            for phase in ("configure", "init", "integrate"):
                if not hasattr(plugin, phase):
                    logger.debug("⏭ %s: нет фазы %s", name, phase)
                    continue

                method = getattr(plugin, phase)

                try:
                    sig = inspect.signature(method)
                    kwargs = (
                        {"settings": settings} if "settings" in sig.parameters else {}
                    )

                    if inspect.iscoroutinefunction(method):
                        await method(**kwargs)
                    else:
                        method(**kwargs)
                    logger.debug("✅ %s: фаза %s завершена", name, phase)
                except (ValueError, TypeError) as e:
                    logger.error(
                        "🔴 Ошибка при анализе сигнатуры или вызове %s.%s: %s",
                        name,
                        phase,
                        e,
                    )

    def healthcheck(self) -> dict:
        return {
            name: plugin.healthcheck() if hasattr(plugin, "healthcheck") else "unknown"
            for name, plugin in self.plugins.items()
        }
