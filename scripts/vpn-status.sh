#!/bin/bash

# VPN Icon Configuration
VPN_ICON="󰌾"  # Network secure icon (Nerd Font)
VPN_ICON_COLOR="#000000"

# Check NordVPN status
status=$(/usr/bin/nordvpn status 2>/dev/null)

if echo "$status" | grep -q "Connected"; then
    # Connected to NordVPN - show shield icon with tooltip
    server=$(echo "$status" | grep "Server:" | awk '{print $2, $3}')
    country=$(echo "$status" | grep "Country:" | awk '{print $2}')
    echo "{\"text\": \"$VPN_ICON\", \"class\": \"vpn-connected\", \"tooltip\": \"NordVPN Connected\n$server\n$country\"}"
else
    # Not connected
    echo '{"text": "", "class": "vpn-disconnected", "tooltip": "VPN Disconnected"}'
fi
