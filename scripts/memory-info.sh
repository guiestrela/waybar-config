#!/bin/bash
# Memory Info Script for Waybar
# Returns JSON with memory usage

mem=$(free -m | grep Mem)
total=$(echo $mem | awk '{print $2}')
used=$(echo $mem | awk '{print $3}')
percent=$((used * 100 / total))

# Format output
if [ $used -gt 1024 ]; then
    used_gb=$(echo "scale=1; $used/1024" | bc)
    total_gb=$(echo "scale=1; $total/1024" | bc)
    text="${used_gb}G"
    tooltip="Memory: ${used_gb}G / ${total_gb}G"
else
    text="${used}M"
    tooltip="Memory: ${used}M / ${total}M"
fi

echo "{\"text\": \"${text}\", \"tooltip\": \"${tooltip}\"}"
