#!/bin/bash

set -euo pipefail

# === Configuration ===
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly TEMPLATE_PATH="$SCRIPT_DIR/systemd/daemon.service.template"
readonly WORKING_DIR="/opt/tgnms"
readonly VENV_DIR="$WORKING_DIR/venv"
readonly USER="tgnms"
readonly GROUP="tgnms"
readonly LOGS_DIR="$WORKING_DIR/logs"
readonly DATA_DIR="$WORKING_DIR/data"
readonly ROLES=("api" "bot" "scheduler")

# === Locale detection ===
detect_locale() {
    case "${LANG:-${LC_MESSAGES:-en_US}}" in
        ru*) echo "ru" ;;
        *)   echo "en" ;;
    esac
}
readonly LOCALE=$(detect_locale)

# === Message function ===
msg() {
    local key=$1
    local lang=${2:-$LOCALE}
    local message_key="${key}/${lang}"

    declare -A messages=(
        ["must_be_root/en"]="Error: This script must be run as root."
        ["must_be_root/ru"]="Ошибка: скрипт должен быть запущен от имени root."
        ["checking_user/en"]="Checking user \"$USER\"..."
        ["checking_user/ru"]="Проверка пользователя \"$USER\"..."
        ["creating_user/en"]="User not found. Creating user and group..."
        ["creating_user/ru"]="Пользователь не найден. Создание пользователя и группы..."
        ["user_exists/en"]="User already exists."
        ["user_exists/ru"]="Пользователь уже существует."
        ["group_created/en"]="Group \"$GROUP\" created."
        ["group_created/ru"]="Группа \"$GROUP\" создана."
        ["group_exists/en"]="Group already exists."
        ["group_exists/ru"]="Группа уже существует."
        ["creating_unit/en"]="Creating systemd unit file..."
        ["creating_unit/ru"]="Создание unit-файла systemd..."
        ["unit_created/en"]="Unit file created: %s"
        ["unit_created/ru"]="Unit-файл создан: %s"
        ["creating_dirs/en"]="Creating log and data directories..."
        ["creating_dirs/ru"]="Создание директорий логов и данных..."
        ["dirs_created/en"]="Directories created successfully."
        ["dirs_created/ru"]="Директории успешно созданы."
        ["setting_permissions/en"]="Setting permissions on working directory..."
        ["setting_permissions/ru"]="Назначение прав доступа к рабочей директории..."
        ["perms_set/en"]="Permissions set successfully."
        ["perms_set/ru"]="Права успешно установлены."
        ["reloading_systemd/en"]="Reloading systemd..."
        ["reloading_systemd/ru"]="Перезагрузка systemd..."
        ["enabling_service/en"]="Enabling service..."
        ["enabling_service/ru"]="Включение сервиса..."
        ["starting_service/en"]="Starting service..."
        ["starting_service/ru"]="Запуск сервиса..."
        ["service_status/en"]="Current service status:"
        ["service_status/ru"]="Текущий статус сервиса:"
        ["setup_complete/en"]="Setup complete."
        ["setup_complete/ru"]="Настройка завершена."
    )

    if [[ -n "${messages[$message_key]+set}" ]]; then
        printf "${messages[$message_key]}" "${@:2}"
        echo
    else
        echo "[$lang] Message key not found: $message_key" >&2
    fi
}


# === Check root ===
if [[ $(id -u) -ne 0 ]]; then
    msg must_be_root >&2
    exit 1
fi

# === Create user/group ===
msg checking_user
if ! id "$USER" &>/dev/null; then
    msg creating_user
    if ! getent group "$GROUP" &>/dev/null; then
        groupadd "$GROUP"
        msg group_created
    else
        msg group_exists
    fi
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

# === Generate unit files from template ===
msg creating_unit
for ROLE in "${ROLES[@]}"; do
    ROLE_SERVICE="tgnms-${ROLE}.service"
    SERVICE_FILE_PATH="/etc/systemd/system/$ROLE_SERVICE"
    
    sed \
        -e "s|{{USER}}|$USER|g" \
        -e "s|{{GROUP}}|$GROUP|g" \
        -e "s|{{WORKING_DIR}}|$WORKING_DIR|g" \
        -e "s|{{VENV_DIR}}|$VENV_DIR|g" \
        -e "s|{{LOGS_DIR}}|$LOGS_DIR|g" \
        -e "s|{{DATA_DIR}}|$DATA_DIR|g" \
        -e "s|{{ROLE}}|${ROLE}|g" \
        "$TEMPLATE_PATH" > "$SERVICE_FILE_PATH"
    
    msg unit_created "$SERVICE_FILE_PATH"
done

# === Create directories ===
msg creating_dirs
install -d -o "$USER" -g "$GROUP" -m 755 "$LOGS_DIR"
install -d -o "$USER" -g "$GROUP" -m 755 "$DATA_DIR"
msg dirs_created

# === Set permissions ===
msg setting_permissions
chown -R "$USER:$GROUP" "$WORKING_DIR"
find "$WORKING_DIR" \( -path "$LOGS_DIR" -o -path "$DATA_DIR" \) -prune -o -exec chown "$USER:$GROUP" {} +
msg perms_set

# === Systemd operations ===
msg reloading_systemd
systemctl daemon-reload

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