#!/usr/bin/env bash

STATE_FILE="${XDG_CACHE_HOME:-$HOME/.cache}/waybar-cpu-info.state"
mkdir -p "$(dirname "$STATE_FILE")"

declare -A prev_idle_core prev_total_core core_usage_map
prev_idle=0
prev_total=0

if [[ -f "$STATE_FILE" ]]; then
    while read -r kind cpu idle total; do
        if [[ "$kind" == "total" ]]; then
            prev_idle=$idle
            prev_total=$total
        elif [[ "$kind" == "core" ]]; then
            prev_idle_core[$cpu]=$idle
            prev_total_core[$cpu]=$total
        fi
    done < "$STATE_FILE"
fi

current_state=()
USAGE=0
max_core_num=-1

while read -r cpu user nice system idle iowait irq softirq steal _; do
    [[ "$cpu" =~ ^cpu([0-9]+)?$ ]] || continue

    now_idle=$((idle + iowait))
    now_total=$((user + nice + system + idle + iowait + irq + softirq + steal))

    if [[ "$cpu" == "cpu" ]]; then
        if (( prev_total > 0 && now_total > prev_total )); then
            diff_idle=$((now_idle - prev_idle))
            diff_total=$((now_total - prev_total))
            if (( diff_total > 0 )); then
                USAGE=$((100 * (diff_total - diff_idle) / diff_total))
            fi
        fi
        current_state+=("total cpu $now_idle $now_total")
        continue
    fi

    core_usage=0
    if [[ -n "${prev_total_core[$cpu]:-}" ]] && (( now_total > prev_total_core[$cpu] )); then
        diff_idle_core=$((now_idle - prev_idle_core[$cpu]))
        diff_total_core=$((now_total - prev_total_core[$cpu]))
        if (( diff_total_core > 0 )); then
            core_usage=$((100 * (diff_total_core - diff_idle_core) / diff_total_core))
        fi
    fi

    core_num=${cpu#cpu}
    core_usage_map[$core_num]=$core_usage
    (( core_num > max_core_num )) && max_core_num=$core_num
    current_state+=("core $cpu $now_idle $now_total")
done < /proc/stat

printf '%s\n' "${current_state[@]}" > "$STATE_FILE"

# ===== 2. Temperatura geral (alinha com btop: Package/Tctl) =====
TEMP_FILE=""
for f in /sys/class/hwmon/hwmon*/temp*_input; do
    [[ -e "$f" ]] || continue
    hwmon_dir=$(dirname "$f")
    hwmon_name=$(cat "$hwmon_dir/name" 2>/dev/null || echo "")
    label=$(cat "${f%_input}_label" 2>/dev/null || echo "")
    if [[ "$hwmon_name" =~ ^(coretemp|k10temp)$ ]] && [[ "$label" =~ ^(Package[[:space:]]id|Tctl|Tdie) ]]; then
        TEMP_FILE="$f"
        break
    fi
done

if [[ -z "$TEMP_FILE" ]]; then
    for d in /sys/class/hwmon/hwmon*; do
        [[ -e "$d/name" ]] || continue
        hwmon_name=$(cat "$d/name" 2>/dev/null || echo "")
        if [[ "$hwmon_name" =~ ^(coretemp|k10temp)$ ]] && [[ -e "$d/temp1_input" ]]; then
            TEMP_FILE="$d/temp1_input"
            break
        fi
    done
fi

if [[ -z "$TEMP_FILE" ]]; then
    TEMP_FILE=$(ls /sys/class/hwmon/hwmon*/temp1_input 2>/dev/null | head -n 1)
fi

TEMP=$(( $(cat "$TEMP_FILE" 2>/dev/null || echo 0) / 1000 ))

CORES_CPU=""
for ((i = 0; i <= max_core_num; i++)); do
    core_usage=${core_usage_map[$i]:-0}
    CORES_CPU+="Core $i: ${core_usage}%\\n"
done

# ===== 4. Estilo =====
ICON=""
CLASS="normal"
[ "$TEMP" -gt 75 ] && CLASS="warning"
[ "$TEMP" -gt 85 ] && CLASS="critical"

# ===== 5. JSON para Waybar =====
echo "{\"text\":\"$ICON $USAGE%\",\"tooltip\":\"Total Usage: $USAGE%\\nCPU Temp: ${TEMP}°C\\n\\nPer-Core Usage:\\n$CORES_CPU\",\"class\":\"$CLASS\",\"percentage\":$USAGE}"
