#!/bin/bash
# CPU Info Script for Waybar
# Returns JSON with CPU usage percentage

# Option 1: Using top
# cpu=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d. -f1)
# echo "{\"text\": \"${cpu}%\", \"tooltip\": \"CPU: ${cpu}%\"}"

# Option 2: Using mpstat (requires sysstat)
# cpu=$(mpstat 1 1 | awk '/Average/ {print 100 - $NF}')
# echo "{\"text\": \"${cpu}%\", \"tooltip\": \"CPU: ${cpu}%\"}"

# Option 3: Using /proc/stat (pure bash)
read cpu < /proc/stat
cpu=${cpu#cpu }
set -- $cpu
idle=$4
total=0
for val; do total=$((total+val)); done
sleep 0.5
read cpu2 < /proc/stat
cpu2=${cpu2#cpu }
set -- $cpu2
idle2=$4
total2=0
for val; do total2=$((total2+val)); done
diff_idle=$((idle2-idle))
diff_total=$((total2-total))
usage=$((100*(diff_total-diff_idle)/diff_total))

echo "{\"text\": \"${usage}%\", \"tooltip\": \"CPU Usage: ${usage}%\"}"
