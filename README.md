# AIO TgNSA

Backend и Telegram-бот для сетевой эксплуатации и администрирования инфраструктуры TgNSA.

Проект объединяет HTTP API на FastAPI, Telegram-бота на aiogram, сетевые диагностические инструменты, SNMP-операции, управление пользователями и подсистему ERTM для учета оборудования, портов и абонентов.

> Документация ниже составлена по фактической структуре и коду репозитория, а не по ранее существовавшему описанию проекта.

## Возможности

### Telegram-бот

Бот работает через long polling Telegram Bot API и содержит отдельные обработчики и middleware для основных сценариев:

- главное меню и навигация;
- авторизация и профиль пользователя;
- управление пользователями;
- административная панель;
- задачи и менеджер задач;
- запросы на обслуживание и массовые инциденты;
- массовая рассылка;
- сетевые диагностические операции;
- ERTM;
- системная информация, мониторинг и логи.

В меню реализованы, в частности:

- P2P-калькулятор;
- CIDR/подсетевой калькулятор;
- проверка доступности устройств через Ping;
- получение DDM-информации;
- VLAN и состояние портов;
- LLDP;
- MAC-таблица;
- измерение длины кабеля;
- работа с оборудованием ERTM.

### Сетевые инструменты

Код содержит отдельный слой утилит для сетевой работы и SNMP. SNMP-функции поддерживают получение одиночных и множественных OID, а ERTM использует SNMP для получения MAC-таблиц и сопоставления MAC-адресов с интерфейсами.

Для MAC-таблицы предусмотрено разделение интерфейсов на access/trunk на основании количества обнаруженных MAC-адресов.

### ERTM

ERTM — локальная подсистема учета сетевого оборудования:

- устройства;
- порты устройств;
- абоненты;
- географические координаты оборудования;
- адреса установки;
- связь `Device -> Port -> Subscriber`;
- получение оборудования из SQLite;
- добавление устройств, портов и абонентов;
- расчет расстояния между координатами.

Модель устройства содержит host, vendor, системное имя, модель, latitude, longitude и address. Для устройства предусмотрено уникальное ограничение по комбинации `host + sys_name + model`.

### HTTP API

API реализован на FastAPI.

Базовые маршруты регистрируются с префиксом `/api`.

| Метод | Endpoint | Назначение |
|---|---|---|
| POST | `/login` | Авторизация пользователя и выдача JWT |
| GET | `/api/` | Информация о приложении и зарегистрированных маршрутах |
| GET | `/api/ping` | Проверка доступности API |
| POST | `/api/send_message` | Отправка сообщения Telegram-пользователю |
| POST | `/api/broadcast` | Массовая отправка сообщений |
| POST | `/api/start_bot` | Управление запуском бота |
| POST | `/api/stop_bot` | Управление остановкой бота |
| POST | `/api/restart_bot` | Управление перезапуском бота |
| GET | `/api/users` | Получение пользователей |
| GET | `/api/user/{id}` | Получение пользователя по Telegram ID |
| PUT | `/api/user/{id}` | Обновление пользователя |
| DELETE | `/api/user/{id}` | Удаление пользователя |
| GET | `/api/configs` | Получение конфигурации |
| POST | `/api/configs` | Изменение параметра конфигурации |
| GET | `/api/config/{key}` | Получение отдельного параметра |
| POST | `/api/config/export` | Экспорт конфигурации |
| POST | `/api/config/import` | Endpoint импорта конфигурации |
| POST | `/api/config/update` | Изменение переменной `.env` |
| GET | `/api/health/status` | Состояние компонентов |
| GET | `/api/health/report` | JSON-отчет о состоянии системы |
| GET | `/api/health/report/html` | HTML-отчет о состоянии системы |
| GET | `/api/health/component/{name}` | Состояние отдельного компонента |
| POST | `/api/health/check` | Запуск полной проверки состояния |
| GET | `/api/devices` | Список устройств ERTM |
| POST | `/api/devices` | Добавление устройства |
| GET | `/api/ports` | Список портов |
| POST | `/api/ports` | Добавление порта |
| GET | `/api/subscribers` | Список абонентов |
| POST | `/api/subscribers` | Добавление абонента |

Актуальная интерактивная документация FastAPI доступна после запуска по `/docs`, OpenAPI-схема — `/openapi.json`.

## Архитектура

```text
Telegram
   |
   v
aiogram Dispatcher
   |
   +-- handlers
   +-- middlewares
   +-- FSM storage
   |
   v
BotManager

HTTP client
   |
   v
FastAPI
   |
   +-- AuthMiddleware (JWT)
   +-- /login
   +-- /api/*
          |
          +-- Index
          +-- UserManager
          +-- ConfigManager
          +-- HealthManager
          +-- SubscriberManager

ERTM
 |
 +-- SQLAlchemy
 |     |
 |     +-- SQLite: data/ertm.db
 |
 +-- Device
 +-- Port
 +-- Subscriber
 |
 +-- SNMP
```

## Хранилища

FSM-хранилище Telegram-бота выбирается конфигурацией:

1. Redis — если `USE_REDIS=true`;
2. MongoDB — если `USE_MONGODB=true`;
3. MemoryStorage — резервный вариант.

ERTM использует SQLite через SQLAlchemy. По умолчанию база создается как:

```text
data/ertm.db
```

Основной конфигурационный слой также содержит настройки для SQLite `data/app.db`, MongoDB, Redis, Firebase и SMTP; фактическое использование зависит от соответствующего модуля и переменных окружения.

## Аутентификация

HTTP API защищается middleware JWT.

По умолчанию без JWT доступны:

- `/login`;
- `/docs`;
- `/openapi.json`;
- `/api/ping`.

Для защищенных запросов используется заголовок:

```http
Authorization: Bearer <JWT>
```

Алгоритм JWT в текущей реализации — `HS256`.

Время жизни access token задается `ACCESS_TOKEN_EXPIRATION` и по умолчанию составляет `15m`.

## Конфигурация

Конфигурация загружается из `.env` и переменных окружения.

Минимальный набор для запуска зависит от используемых функций, но для полноценной работы необходимы как минимум секрет JWT и токен Telegram-бота:

```dotenv
APP_NAME=TgNSA
VERSION=0.1.0
SECRET_KEY=change-me
API_TOKEN=<telegram-bot-token>

DEFAULT_LOCALE=ru_RU.UTF-8
DEFAULT_TIMEZONE=UTC

USE_REDIS=false
REDIS_URL=redis://127.0.0.1:6379/

USE_MONGODB=false
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=fsm-aio

FIREBASE_DATABASE_URL=https://ttcnsa-default-rtdb.asia-southeast1.firebasedatabase.app
```

Для production рекомендуется задавать секреты только через окружение/секрет-хранилище и не коммитить `.env` и `serviceAccountKey.json`.

## Установка

Проект рассчитан на Python 3.10; этот же runtime используется в GitHub Actions.

```bash
git clone https://github.com/drycov/aio.tgnsa.ru.git
cd aio.tgnsa.ru

python3.10 -m venv venv
source venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

Перед запуском:

1. создайте `.env`;
2. задайте `SECRET_KEY`;
3. задайте `API_TOKEN`;
4. при использовании Firebase разместите `serviceAccountKey.json` в корне проекта;
5. убедитесь, что пользователь процесса имеет права на `data/` и `logs/`.

## Запуск

### Development

```bash
python main.py
```

Параметры:

```bash
python main.py --reload
python main.py --workers 2
```

По текущему коду Uvicorn слушает `127.0.0.1:8000`.

### Uvicorn

```bash
uvicorn main:app --host 127.0.0.1 --port 8000
```

### systemd

В репозитории присутствует `aio_tgnsa.service`. Он рассчитан на установку проекта в `/opt/tgnms` и запуск от пользователя/группы `tgnms`:

```text
/opt/tgnms/venv/bin/python /opt/tgnms/main.py
```

Unit настроен на автоматический перезапуск при падении и ограничивает ряд системных ресурсов.

## Проверка

В репозитории настроен GitHub Actions workflow для Python 3.10.

CI выполняет:

```bash
pip install -r requirements.txt
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --max-complexity=10 --max-line-length=127 --statistics
pytest --maxfail=1 --disable-warnings
```

Локально рекомендуется запускать те же проверки перед изменениями:

```bash
python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
python -m flake8 . --count --max-complexity=10 --max-line-length=127 --statistics
pytest --maxfail=1 --disable-warnings
```

## Структура проекта

```text
.
├── api/
│   ├── app.py
│   ├── database.py
│   ├── routes/
│   │   ├── index/
│   │   ├── user_manager/
│   │   ├── config_manager/
│   │   ├── health_manager/
│   │   ├── subscriber_manager/
│   │   └── tasks_manager/
│   └── services/
├── bot/
│   ├── bot_instance.py
│   ├── bot_module.py
│   ├── constants/
│   ├── handlers/
│   ├── middlewares/
│   ├── models/
│   └── utils/
├── ertm/
│   ├── ertm.py
│   ├── models/
│   └── schemas/
├── config.py
├── healthy.py
├── housekeeper.py
├── main.py
├── requirements.txt
└── aio_tgnsa.service
```

## Основные компоненты

### `main.py`

Создает экземпляр FastAPI-приложения, инициализирует поиск производителей MAC-адресов и запускает Uvicorn.

### `api/app.py`

Содержит основной lifecycle FastAPI, JWT middleware, Firebase initialization, scheduler, health manager и управление Telegram-ботом.

### `bot/bot_instance.py`

Создает `Bot` и `Dispatcher`, выбирает FSM storage и инициализирует ERTM.

### `bot/bot_module.py`

`BotManager` отвечает за настройку handlers/middleware, запуск polling, остановку и graceful shutdown.

### `ertm/ertm.py`

Содержит доменную логику ERTM, работу с SQLAlchemy/SQLite, управление устройствами/портами/абонентами и обработку SNMP MAC-таблиц.

### `healthy.py`

Подсистема проверки состояния компонентов, генерации JSON/HTML отчетов и выполнения health checks.

### `housekeeper.py`

Фоновая подсистема обслуживания, параметры которой задаются через `HOUSEKEEPER_*`.

## Зависимости

Основные используемые библиотеки:

- FastAPI / Starlette / Uvicorn — HTTP API;
- aiogram — Telegram Bot API;
- Pydantic — модели API;
- SQLAlchemy — работа с SQLite;
- Redis / aioredis — Redis storage и инфраструктурные операции;
- Motor / PyMongo — MongoDB storage;
- Firebase Admin SDK — Firebase;
- python-jose / PyJWT — JWT;
- APScheduler — фоновые задачи;
- puresnmp / pyasn1 — SNMP;
- ping3 — ICMP-проверки;
- netaddr — сетевые операции;
- Loguru — логирование;
- pandas / tabulate / prettytable — подготовка табличных данных.

Полный список зафиксирован в `requirements.txt`.

## Безопасность

При эксплуатации проекта следует отдельно проверить:

- отсутствие секретов и service account ключей в Git;
- значение и длину `SECRET_KEY`;
- допустимость публикации `/docs` и конфигурационных endpoint'ов;
- права доступа к `/api/configs`, `/api/config/{key}` и `/api/config/update`;
- ограничения массовой рассылки;
- SNMP community strings;
- права пользователя systemd на `data/` и `logs/`;
- хранение FSM в MemoryStorage при production-развертывании.

Особенно важно: текущий API содержит endpoint'ы управления конфигурацией и массовой отправки Telegram-сообщений, поэтому они должны быть защищены сетевыми и прикладными механизмами доступа в production.

## Ограничения текущей реализации

Документация намеренно не скрывает участки кода, которые требуют дальнейшей доработки:

- endpoint `/api/config/import` присутствует, но его реализация фактически не завершена;
- `/api/start_bot`, `/api/stop_bot` и `/api/restart_bot` вызывают методы `start_bot_task`, `stop_bot_task` и `restart_bot_task`, тогда как в показанном `API` реализован интерфейс `manage_bot_task`; эти маршруты требуют согласования перед эксплуатацией;
- `main.py` запускает Uvicorn на loopback (`127.0.0.1`), поэтому прямой внешний доступ без reverse proxy не предусмотрен;
- systemd unit использует отдельный путь `/opt/tgnms`, который должен совпадать с фактическим deployment path;
- workflow CI ожидает наличие Flake8 и pytest в окружении, при этом они не зафиксированы в `requirements.txt`.

Эти пункты относятся к фактическому состоянию исходного кода и не являются частью функционального контракта проекта.

## Лицензия

В конфигурации проекта указана лицензия MIT.

## Репозиторий

https://github.com/drycov/aio.tgnsa.ru
