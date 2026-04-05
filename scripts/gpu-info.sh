#!/bin/bash
# GPU Info Script for Waybar
# Returns JSON with GPU temperature/info

# Option 1: NVIDIA
# if command -v nvidia-smi &> /dev/null; then
#     temp=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader)
#     util=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader)
#     echo "{\"text\": \"${temp}°C\", \"tooltip\": \"GPU: ${temp}°C, ${util}%\"}"
# fi

# Option 2: AMD (rocm-smi or sensors)
if command -v rocm-smi &> /dev/null; then
    temp=$(rocm-smi --showtemp | grep "temperature" | awk '{print $3}' | head -1 | tr -d "'")
    echo "{\"text\": \"${temp}°C\", \"tooltip\": \"GPU Temperature: ${temp}°C\"}"
elif command -v sensors &> /dev/null; then
    temp=$(sensors | grep "edge:" | awk '{print $2}' | tr -d '+°C')
    if [ -n "$temp" ]; then
        echo "{\"text\": \"${temp}°C\", \"tooltip\": \"GPU Temperature: ${temp}°C\"}"
    else
        echo "{\"text\": \"N/A\", \"tooltip\": \"GPU: Not detected\"}"
    fi
else
    echo "{\"text\": \"N/A\", \"tooltip\": \"GPU: No monitoring tool\"}"
fi
