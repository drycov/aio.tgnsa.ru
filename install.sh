#!/bin/bash

set -euo pipefail

# === Конфигурация ===
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_PATH="$SCRIPT_DIR/../systemd/daemon.service.template"
SERVICE_NAME="tgnms-daemon.service"
SERVICE_FILE_PATH="/etc/systemd/system/$SERVICE_NAME"
WORKING_DIR="/opt/tgnms"
VENV_DIR="$WORKING_DIR/venv"
USER="tgnms"
GROUP="tgnms"
LOGS_DIR="$WORKING_DIR/logs"
DATA_DIR="$WORKING_DIR/data"
ROLES=("api" "bot" "scheduler")

# === Определение локали ===
detect_locale() {
  local lang="${LANG:-${LC_MESSAGES:-en_US}}"
  case "$lang" in
  ru*) echo "ru" ;;
  *) echo "en" ;;
  esac
}
LOCALE=$(detect_locale)

# === Функция сообщений ===
msg() {
  case "$1" in
  must_be_root)
    [[ "$LOCALE" == "ru" ]] && echo "Ошибка: скрипт должен быть запущен от имени root." || echo "Error: This script must be run as root."
    ;;
  checking_user)
    [[ "$LOCALE" == "ru" ]] && echo "Проверка пользователя \"$USER\"..." || echo "Checking user \"$USER\"..."
    ;;
  creating_user)
    [[ "$LOCALE" == "ru" ]] && echo "Пользователь не найден. Создание пользователя и группы..." || echo "User not found. Creating user and group..."
    ;;
  user_exists)
    [[ "$LOCALE" == "ru" ]] && echo "Пользователь уже существует." || echo "User already exists."
    ;;
  group_created)
    [[ "$LOCALE" == "ru" ]] && echo "Группа \"$GROUP\" создана." || echo "Group \"$GROUP\" created."
    ;;
  group_exists)
    [[ "$LOCALE" == "ru" ]] && echo "Группа уже существует." || echo "Group already exists."
    ;;
  creating_unit)
    [[ "$LOCALE" == "ru" ]] && echo "Создание unit-файла systemd..." || echo "Creating systemd unit file..."
    ;;
  unit_created)
    [[ "$LOCALE" == "ru" ]] && echo "Unit-файл создан: $SERVICE_FILE_PATH" || echo "Unit file created: $SERVICE_FILE_PATH"
    ;;
  creating_dirs)
    [[ "$LOCALE" == "ru" ]] && echo "Создание директорий логов и данных..." || echo "Creating log and data directories..."
    ;;
  dirs_created)
    [[ "$LOCALE" == "ru" ]] && echo "Директории успешно созданы." || echo "Directories created successfully."
    ;;
  setting_permissions)
    [[ "$LOCALE" == "ru" ]] && echo "Назначение прав доступа к рабочей директории..." || echo "Setting permissions on working directory..."
    ;;
  perms_set)
    [[ "$LOCALE" == "ru" ]] && echo "Права успешно установлены." || echo "Permissions set successfully."
    ;;
  reloading_systemd)
    [[ "$LOCALE" == "ru" ]] && echo "Перезагрузка systemd..." || echo "Reloading systemd..."
    ;;
  enabling_service)
    [[ "$LOCALE" == "ru" ]] && echo "Включение сервиса..." || echo "Enabling service..."
    ;;
  starting_service)
    [[ "$LOCALE" == "ru" ]] && echo "Запуск сервиса..." || echo "Starting service..."
    ;;
  service_status)
    [[ "$LOCALE" == "ru" ]] && echo "Текущий статус сервиса:" || echo "Current service status:"
    ;;
  setup_complete)
    [[ "$LOCALE" == "ru" ]] && echo "Настройка завершена." || echo "Setup complete."
    ;;
  esac
}

# === Проверка root ===
if [[ $(id -u) -ne 0 ]]; then
  msg must_be_root >&2
  exit 1
fi

# === Создание пользователя/группы ===
msg checking_user
if ! id "$USER" &>/dev/null; then
  msg creating_user
  getent group "$GROUP" &>/dev/null || groupadd "$GROUP"
  useradd --system --no-create-home --gid "$GROUP" "$USER"
else
  msg user_exists
  if ! getent group "$GROUP" &>/dev/null; then
    groupadd "$GROUP"
    msg group_created
  else
    msg group_exists
  fi
fi

# === Генерация unit-файла из шаблона ===
msg creating_unit
# sed \
#   -e "s|{{USER}}|$USER|g" \
#   -e "s|{{GROUP}}|$GROUP|g" \
#   -e "s|{{WORKING_DIR}}|$WORKING_DIR|g" \
#   -e "s|{{VENV_DIR}}|$VENV_DIR|g" \
#   -e "s|{{LOGS_DIR}}|$LOGS_DIR|g" \
#   -e "s|{{DATA_DIR}}|$DATA_DIR|g" \
#   "systemd/tgnms-daemon.service.template" >"$SERVICE_FILE_PATH"
for ROLE in "${ROLES[@]}"; do
  ROLE_SERVICE="tgnms-${ROLE}.service"
  sed \
    -e "s|{{USER}}|$USER|g" \
    -e "s|{{GROUP}}|$GROUP|g" \
    -e "s|{{WORKING_DIR}}|$WORKING_DIR|g" \
    -e "s|{{VENV_DIR}}|$VENV_DIR|g" \
    -e "s|{{LOGS_DIR}}|$LOGS_DIR|g" \
    -e "s|{{DATA_DIR}}|$DATA_DIR|g" \
    -e "s|{{ROLE}}|${ROLE}|g"
    "$TEMPLATE_PATH" >"/etc/systemd/system/$ROLE_SERVICE"
done
msg unit_created



# === Создание директорий ===
msg creating_dirs
install -d -o "$USER" -g "$GROUP" -m 755 "$LOGS_DIR"
install -d -o "$USER" -g "$GROUP" -m 755 "$DATA_DIR"
msg dirs_created

# === Назначение прав ===
msg setting_permissions
chown -R "$USER:$GROUP" "$WORKING_DIR"
find "$WORKING_DIR" \( -path "$LOGS_DIR" -o -path "$DATA_DIR" \) -prune -o -exec chown "$USER:$GROUP" {} +
msg perms_set

# === Systemd ===
msg reloading_systemd
systemctl daemon-reload

# msg enabling_service
# systemctl enable "$SERVICE_NAME"

# msg starting_service
# systemctl start "$SERVICE_NAME"

# msg service_status
# systemctl status "$SERVICE_NAME" --no-pager

for ROLE in "${ROLES[@]}"; do
  ROLE_SERVICE="tgnms-${ROLE}.service"

  msg enabling_service
  systemctl enable "$ROLE_SERVICE"

  msg starting_service
  systemctl start "$ROLE_SERVICE"

  msg service_status
  systemctl status "$ROLE_SERVICE" --no-pager
done


msg setup_complete
