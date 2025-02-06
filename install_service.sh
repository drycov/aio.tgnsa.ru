#!/bin/bash

# Параметры
SERVICE_NAME="aio_tgnsa.service"
SERVICE_FILE_PATH="/etc/systemd/system/$SERVICE_NAME"
WORKING_DIR="/opt/aio.tgnsa.ru"
VENV_DIR="$WORKING_DIR/venv"
USER="nobody"
GROUP="nogroup"
LOGS_DIR="$WORKING_DIR/logs"
DATA_DIR="$WORKING_DIR/data"

# Убедитесь, что скрипт выполняется с правами суперпользователя
if [[ $(id -u) -ne 0 ]]; then
    echo "Этот скрипт должен быть выполнен с правами суперпользователя (root)."
    exit 1
fi

# Создание юнит-файла для systemd
echo "Создание юнит-файла для сервиса $SERVICE_NAME..."

cat > $SERVICE_FILE_PATH << EOF
[Unit]
Description=Aio Tgnsa Service
After=network.target

[Service]
User=$USER
Group=$GROUP
WorkingDirectory=$WORKING_DIR
ExecStart=$VENV_DIR/bin/python $WORKING_DIR/main.py
Restart=always
RestartSec=3s
StandardOutput=journal
StandardError=journal
Environment="PYTHONUNBUFFERED=1"
Environment="PATH=$VENV_DIR/bin:\$PATH"
LimitNOFILE=65536
LimitNPROC=512
ProtectSystem=full
ProtectHome=yes
NoNewPrivileges=true
PrivateTmp=true
ReadWritePaths=$LOGS_DIR
ReadWritePaths=$DATA_DIR
PrivateDevices=true

[Install]
WantedBy=multi-user.target
EOF

# Убедимся, что директории для логов и данных существуют
echo "Проверка и создание директорий $LOGS_DIR и $DATA_DIR..."
mkdir -p $LOGS_DIR $DATA_DIR

# Установка прав доступа
echo "Установка прав доступа на директории..."
chown -R $USER:$GROUP $WORKING_DIR
chmod -R 755 $LOGS_DIR $DATA_DIR

# Перезагрузка systemd и запуск сервиса
echo "Перезагрузка systemd и запуск сервиса..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

echo "Сервис $SERVICE_NAME успешно настроен и запущен."
