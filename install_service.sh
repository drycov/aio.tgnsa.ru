#!/bin/bash

# Parameters
SERVICE_NAME="aio_tgnsa.service"
SERVICE_FILE_PATH="/etc/systemd/system/$SERVICE_NAME"
WORKING_DIR="/opt/tgnms"
VENV_DIR="$WORKING_DIR/venv"
USER="tgnms"
GROUP="tgnms"
LOGS_DIR="$WORKING_DIR/logs"
DATA_DIR="$WORKING_DIR/data"

# Make sure the script is run with root privileges
if [[ $(id -u) -ne 0 ]]; then
echo "This script must be run with root privileges." >&2
exit 1
fi

# Check if the user and group exist
echo "Checking user $USER..."
if ! id "$USER" &>/dev/null; then
echo "User $USER not found. Creating user and group $USER..."
if ! getent group "$GROUP" &>/dev/null; then
groupadd "$GROUP" || { echo "Error: Failed to create group $GROUP." >&2; exit 1; }
fi
useradd --system --no-create-home --group "$GROUP" --user-group "$USER" || { echo "Error: Failed to create user $USER." >&2; exit 1; }
echo "User $USER created successfully."
else
echo "User $USER already exists."
if ! getent group "$GROUP" &>/dev/null; then
echo "Group $GROUP not found. Creating group $GROUP..."
groupadd "$GROUP" || { echo "Error: Failed to create group $GROUP." >&2; exit 1; }
echo "Group $GROUP created successfully."
else
echo "Group $GROUP already exists."
fi
fi

# Creating unit file for systemd
echo "Creating unit file for service $SERVICE_NAME in $SERVICE_FILE_PATH..."
cat > "$SERVICE_FILE_PATH" << EOF
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

if [$? -ne 0 ]; then 
echo "Error: Failed to create service unit file." >&2
exit 1
fi
echo "Service unit file created successfully."

# Make sure log and data directories exist and have correct permissions
echo "Checking and creating $LOGS_DIR and $DATA_DIR directories with permissions set..."
install -d -o "$USER" -g "$GROUP" -m 755 "$LOGS_DIR" || { echo "Error: Failed to create log directory $LOGS_DIR." >&2; exit 1; }
install -d -o "$USER" -g "$GROUP" -m 755 "$DATA_DIR" || { echo "Error: Failed to create data directory $DATA_DIR." >&2; exit 1; }
echo "Log and data directories created and permissions set."

# Setting permissions on the working directory, excluding logs and data (they are already processed)
echo "Setting permissions on the working directory $WORKING_DIR..."
chown -R $USER:$GROUP $WORKING_DIR
# Disable recursive permissions for LOGS_DIR and DATA_DIR, since they are already set install -d
find "$WORKING_DIR" ! -path "$LOGS_DIR*" ! -path "$DATA_DIR*" -exec chown $USER:$GROUP {} +
if [ $? -ne 0 ]; then
echo "Warning: Unable to fully set ownership of the working directory." >&2
fi
echo "Permissions on the working directory have been set."

# Restart systemd and start the service
echo "Restarting systemd..."
systemctl daemon-reload || { echo "Error: Failed to restart systemd." >&2; exit 1; }
echo "systemd restarted."

echo "Enabling service $SERVICE_NAME..."
systemctl enable "$SERVICE_NAME" || { echo "Error: Failed to enable service $SERVICE_NAME." >&2; exit 1; }
echo "Service $SERVICE_NAME enabled."

echo "Starting service $SERVICE_NAME..."
systemctl start "$SERVICE_NAME" || { echo "Error: Failed to start service $SERVICE_NAME. Check service logs with 'journalctl -u $SERVICE_NAME'." >&2; exit 1; }
echo "Service $SERVICE_NAME started successfully."

echo "Checking the status of service $SERVICE_NAME..."
systemctl status "$SERVICE_NAME"

echo "Configuration of service $SERVICE_NAME completed."