#!/bin/bash
# VPN Status Script for Waybar
# Returns JSON with VPN connection status

# Option 1: WireGuard
# wg=$(wg show 2>/dev/null)
# if [ -n "$wg" ]; then
#     echo "{\"text\": \"🔒 WG\", \"tooltip\": \"WireGuard: Connected\"}"
# else
#     echo "{\"text\": \"\", \"tooltip\": \"VPN: Disconnected\"}"
# fi

# Option 2: OpenVPN
# if pgrep -x "openvpn" > /dev/null; then
#     echo "{\"text\": \"🔒 VPN\", \"tooltip\": \"OpenVPN: Connected\"}"
# else
#     echo "{\"text\": \"\", \"tooltip\": \"VPN: Disconnected\"}"
# fi

# Option 3: nmcli (NetworkManager)
# vpn=$(nmcli -t -f NAME,TYPE con show --active | grep vpn | cut -d: -f1)
# if [ -n "$vpn" ]; then
#     echo "{\"text\": \"🔒 VPN\", \"tooltip\": \"VPN: $vpn\"}"
# else
#     echo "{\"text\": \"\", \"tooltip\": \"VPN: Disconnected\"}"
# fi

# Default: No VPN configured
echo "{\"text\": \"\", \"tooltip\": \"VPN: Not configured\"}"
