#!/bin/bash
# Idempotent device setup for the DaysSince display.
# Run ON the Pi, from the repo directory:  sudo ./install.sh
# A fresh SD card (Raspberry Pi OS Lite + WiFi + ssh) needs only:
#   sudo apt-get install -y git && git clone https://github.com/Garrulousbrevity/dayssince-device.git
#   cd dayssince-device && sudo ./install.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
PISUGAR_VERSION=2.3.2

echo "== interfaces (SPI, I2C) =="
if command -v raspi-config >/dev/null; then
    raspi-config nonint do_spi 0
    raspi-config nonint do_i2c 0
else
    sed -i 's/^#dtparam=spi=on/dtparam=spi=on/; s/^#dtparam=i2c_arm=on/dtparam=i2c_arm=on/' /boot/firmware/config.txt
fi
modprobe i2c-dev || true
echo i2c-dev > /etc/modules-load.d/i2c-dev.conf

echo "== apt packages =="
apt-get update -qq
apt-get install -y -qq git i2c-tools netcat-openbsd fonts-dejavu-core fonts-firacode \
    python3-requests python3-pil python3-spidev python3-gpiozero python3-lgpio

echo "== pisugar-server =="
# IMPORTANT: the default armhf builds are compiled for ARMv7 and SIGSEGV on the
# Pi Zero W (ARMv6). The armel builds are statically linked and run fine.
if ! systemctl is-active --quiet pisugar-server; then
    dpkg --add-architecture armel
    cd /tmp
    for p in pisugar-server pisugar-poweroff pisugar-programmer; do
        wget -q "https://github.com/PiSugar/pisugar-power-manager-rs/releases/download/v${PISUGAR_VERSION}/${p}_${PISUGAR_VERSION}-1_armel.deb"
    done
    dpkg -i pisugar-server_${PISUGAR_VERSION}-1_armel.deb \
            pisugar-poweroff_${PISUGAR_VERSION}-1_armel.deb \
            pisugar-programmer_${PISUGAR_VERSION}-1_armel.deb
    cd "$REPO_DIR"
    sleep 4
fi
systemctl is-active --quiet pisugar-server || { echo "pisugar-server failed to start"; exit 1; }

pisugar_cmd() {
    echo "$1" | nc -q1 127.0.0.1 8423 | tr -d '\r'
}

echo "== pisugar config =="
pisugar_cmd "rtc_pi2rtc"
# Double-tap = "update now" (re-runs the launcher; also the post-reset instant refresh)
pisugar_cmd "set_button_enable double 1"
pisugar_cmd "set_button_shell double systemctl restart dayssince"

echo "== wifi power-save off (inbound poke latency) =="
CON=$(nmcli -t -f NAME connection show --active | head -n1 || true)
if [ -n "$CON" ]; then
    nmcli connection modify "$CON" 802-11-wireless.powersave 2 || true
fi

echo "== state dir + shutdown permission =="
mkdir -p /var/lib/dayssince
chown pi:pi /var/lib/dayssince
echo "pi ALL=(root) NOPASSWD: /usr/sbin/shutdown" > /etc/sudoers.d/dayssince
chmod 440 /etc/sudoers.d/dayssince

echo "== systemd unit =="
ln -sf "$REPO_DIR/systemd/dayssince.service" /etc/systemd/system/dayssince.service
systemctl daemon-reload
systemctl enable dayssince

echo
echo "Done. Reboot (or 'systemctl start dayssince') to launch."
echo "Emergency hold: 'touch /boot/firmware/dayssince-hold' stops the launcher"
echo "from flashing/shutting down on next boot."
