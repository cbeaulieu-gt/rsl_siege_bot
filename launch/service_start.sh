# Check if the file is already in the service directory and if not copy it there
SERVICE_DIR="/etc/systemd/system"
SERVICE_SCRIPT_SOURCE="$(dirname "$(realpath "$0")")/raid-bot@.service"

LOG_ROTATE_DIR="/etc/logrotate.d"

# Copy logrotate configuration
LOG_ROTATE_SOURCE="$(dirname "$(realpath "$0")")/raid-bot"
dos2unix "$LOG_ROTATE_SOURCE"
if [ ! -f "$LOG_ROTATE_DIR/raid-bot" ]; then
    echo "Copying logrotate configuration to $LOG_ROTATE_DIR"
    sudo cp "$LOG_ROTATE_SOURCE" "$LOG_ROTATE_DIR/"
else
    # Overwrite existing file
    echo "Logrotate configuration already exists in $LOG_ROTATE_DIR, overwriting."
    sudo cp "$LOG_ROTATE_SOURCE" "$LOG_ROTATE_DIR/"
fi

if [ ! -f "$SERVICE_DIR/raid-bot@.service" ]; then
    echo "Copying service file to $SERVICE_DIR"
    sudo cp "$SERVICE_SCRIPT_SOURCE" "$SERVICE_DIR/"
else
    # Overwrite existing file
    echo "Service file already exists in $SERVICE_DIR, overwriting."
    sudo cp "$SERVICE_SCRIPT_SOURCE" "$SERVICE_DIR/"
fi

sudo systemctl daemon-reload
sudo systemctl enable --now raid-bot@personal.service
sudo systemctl enable --now raid-bot@mom.service