# aio.tgnsa.ru

Телеграм-бот и FastAPI-сервис для TGNMS — мониторинга и управления сетью, на базе aiogram и FastAPI.

## 🎯 Цели проекта

- Управление сетью через Telegram: сканирование подсетей, ping-уведомления, меню.
- REST API для внешних интеграций.
- Плагинная архитектура для гибкости и расширяемости.

## ⚙️ Особенности текущего `refactor`

- переработан `PluginManager`: улучшена загрузка, сортировка, перезагрузка, однократная инициализация;
- улучшены `FileStorage` с поддержкой JSON, TOML, YAML и MessagePack; хранение FSM в структуре `./fsm_states/{bot_id}/{user_id}/state.*`;
- улучшены декораторы ошибок для сетевых функций;
- добавлено разделение логики FSM: валидация, хранение, сеть, ping.

## 🚀 Быстрый старт

1. Клонируйте:
    ```bash
    git clone https://github.com/drycov/aio.tgnsa.ru.git
    git checkout refactor
    ```
2. Установите зависимости:
    ```bash
    pip install -r requirements.txt
    ```
3. Настройте `.env` (пример в `.env.example`):
    ```bash
    cp .env.example .env
    ```
4. Запуск:
    - Telegram‑бот:
      ```bash
      python -m app.bot.runner service run bot
      ```
    - REST API:
      ```bash
      python -m app.cli service run api
      ```
    - Планировщик задач:
      ```bash
      python -m app.cli service run scheduler
      ```

## 🧩 Архитектура

- `app/plugins/manager.py` — менеджер плагинов (core, локальные, entrypoint; topological sort; загрузка/перезагрузка).
- `app/plugins/*` — плагины (бот, UI, healthcheck, конфиг).
- `app/bot/runner.py` — точка входа Telegram‑бота (инициализация FSM, плагинов).
- `app/api/server.py` — FastAPI REST интерфейс.
- `app/core/utils/` — вспомогательные компоненты, логирование, декораторы.
- `app/core/config.py` — глобальная конфигурация.

## 📦 Плагины

| Имя            | Описание                             | Зависимости |
|----------------|--------------------------------------|-------------|
| `plugins_ui`   | Основное меню бота                   | —           |
| `healthcheck`  | REST endpoint для мониторинга       | —           |
| `config_viewer`| Просмотр глобального конфига через API | —       |
| `device_check_menu`, `advanced_menu` | Меню проверки устройств и подсетей | — |

## 🛠 Разработка

- ✅ Команда: `refactor/*` — крупные изменения; `feat/*`, `fix/*`, `chore/*`, `test/*`.
- Запускайте `pre-commit` и линтеры перед коммитом.
- Для автокомплита и управления плагинами используется `typer` CLI (`app/cli.py`).

## 📚 Документация

- FSM-хранилище: структура `fsm_states/{bot_id}/{user_id}/state.json`
- Декоратор `@handle_network_error` — централизованная обработка ошибок сетевых операций.
- Сериализация: JSON/TOML/YAML/MessagePack (через `FileStorage.format`).

## ⚠️ Предупреждения

- Для запуска бота требуется Telegram‑токен (`BOT_TOKEN`).
- Используемый формат FSM-хранилища должен соответствовать выбору `format` — при смене формата старые файлы игнорируются.
- Папки FSM создаются автоматически и очищаются при удалении пользователя.

## 📄 Лицензия

MIT © Drycov

---

Спасибо за использование `aio.tgnsa.ru`! contributions приветствуются 🙌
