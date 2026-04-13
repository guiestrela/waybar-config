#!/usr/bin/env bash

# Detecta o card (prioriza card1 que costuma ser a dedicada em laptops)
CARD=""
for c in card1 card0 card2; do
    if [ -d "/sys/class/drm/$c/device/hwmon" ]; then
        CARD="$c"
        break
    fi
done

if [ -z "$CARD" ]; then
    echo "{\"text\": \"No GPU\", \"class\": \"critical\"}"
    exit 1
fi

# Uso de GPU
USAGE=$(cat "/sys/class/drm/$CARD/device/gpu_busy_percent" 2>/dev/null || echo 0)

# VRAM
USED=$(cat "/sys/class/drm/$CARD/device/mem_info_vram_used" 2>/dev/null || echo 0)
TOTAL=$(cat "/sys/class/drm/$CARD/device/mem_info_vram_total" 2>/dev/null || echo 1)
VRAM_PCT=$(( USED * 100 / TOTAL ))

# Temperatura
TEMP_FILE=$(ls /sys/class/drm/$CARD/device/hwmon/hwmon*/temp1_input 2>/dev/null | head -n 1)
TEMP_RAW=$(cat "$TEMP_FILE" 2>/dev/null || echo 0)
TEMP=$(( TEMP_RAW / 1000 ))

# Lógica de Ícones e Classes
ICON="󰢮"
CLASS="normal"

if [ "$TEMP" -gt 80 ]; then
    CLASS="critical"
    ICON="󰈸"
elif [ "$TEMP" -gt 65 ]; then
    CLASS="warning"
fi

# Saída JSON para o Waybar
# text: O que aparece na barra
# tooltip: O que aparece ao passar o mouse
echo "{\"text\": \"$ICON $USAGE%\", \"tooltip\": \"GPU: $USAGE%\nVRAM: $VRAM_PCT%\nTemp: ${TEMP}°C\", \"class\": \"$CLASS\", \"percentage\": $USAGE}"
