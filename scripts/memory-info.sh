#!/usr/bin/env bash

# Extrai dados do /proc/meminfo (em KB)
MEM_TOTAL=$(grep MemTotal /proc/meminfo | awk '{print $2}')
MEM_AVAIL=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
MEM_USED=$((MEM_TOTAL - MEM_AVAIL))

# Cálculo de porcentagem
PERCENTAGE=$(( 100 * MEM_USED / MEM_TOTAL ))

# Conversão para GB (Shell faz apenas inteiros, então usamos awk para decimais no tooltip)
USED_GB=$(awk "BEGIN {printf \"%.1f\", $MEM_USED / 1024 / 1024}")
TOTAL_GB=$(awk "BEGIN {printf \"%.1f\", $MEM_TOTAL / 1024 / 1024}")
AVAIL_GB=$(awk "BEGIN {printf \"%.1f\", $MEM_AVAIL / 1024 / 1024}")

# Swap (Opcional, mas útil no tooltip)
SWAP_TOTAL=$(grep SwapTotal /proc/meminfo | awk '{print $2}')
SWAP_FREE=$(grep SwapFree /proc/meminfo | awk '{print $2}')
SWAP_USED=$((SWAP_TOTAL - SWAP_FREE))
SWAP_GB=$(awk "BEGIN {printf \"%.1f\", $SWAP_USED / 1024 / 1024}")

# Classes de status
CLASS="normal"
if [ "$PERCENTAGE" -gt 90 ]; then
    CLASS="critical"
elif [ "$PERCENTAGE" -gt 70 ]; then
    CLASS="warning"
fi

# Ícone e Saída JSON
ICON=""
TOOLTIP="RAM Usage\\nUsed: ${USED_GB} GB\\nTotal: ${TOTAL_GB} GB\\nAvailable: ${AVAIL_GB} GB\\nUsage: ${PERCENTAGE}%\\n\\nSwap Used: ${SWAP_GB} GB"
ICON=""
echo "{\"text\": \"$ICON $PERCENTAGE%\", \"tooltip\": \"$TOOLTIP\", \"class\": \"$CLASS\", \"percentage\": $PERCENTAGE}"
