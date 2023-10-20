#!/bin/bash

SERVICE_NAME="yeelightble"
SERVICE_DESCRIPTION="Yeelight BLE Service"
SERVICE_EXEC="/usr/local/bin/$SERVICE_NAME"
SERVICE_UNIT_FILE="/etc/systemd/system/$SERVICE_NAME.service"

# Create the service unit file
cat <<EOF > "$SERVICE_UNIT_FILE"
[Unit]
Description=$SERVICE_DESCRIPTION

[Service]
Type=simple
ExecStart=$SERVICE_EXEC
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

# Enable and start the service
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"

# Check the service status
systemctl status "$SERVICE_NAME"
