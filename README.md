# Waybar Configuration

A clean Waybar configuration for Hyprland, based on Omarchy defaults.

## Features

- **Clock Module**: Shows day and time, date in tooltip
- **Weather**: Weather info with wttr.in (no API key needed)
- **System Stats**: CPU, Memory, GPU monitoring
- **Audio**: PulseAudio controls with volume tooltip
- **Network**: WiFi/Ethernet status with connection info
- **Bluetooth**: Device status and battery info
- **Power Profiles**: Quick profile switching
- **Battery**: Multi-battery support with state indicators
- **Backlight**: Brightness control with scroll
- **VPN Status**: Custom script integration
- **Pomodoro Timer**: Focus timer with controls
- **Wallpaper**: Quick wallpaper switching
- **Tray**: Expandable system tray
- **Workspaces**: Hyprland workspace integration

## Installation

### 1. Backup existing config

```bash
mv ~/.config/waybar/config.jsonc ~/.config/waybar/config.jsonc.bak
```

### 2. Copy the config

```bash
# Create scripts directory if it doesn't exist
mkdir -p ~/.config/waybar/scripts

# Copy all files
cp config.jsonc ~/.config/waybar/config.jsonc
cp style.css ~/.config/waybar/style.css
cp scripts/* ~/.config/waybar/scripts/
```

### 3. Required Dependencies

Make sure you have these packages installed:

```bash
# Core
waybar
hyprland

# Optional (for full functionality)
pulseaudio
brightnessctl
bluetooth
networkmanager
power-profiles-daemon
btop
python3
jq
```

### 4. Make scripts executable

```bash
chmod +x ~/.config/waybar/scripts/*.sh
```

### 5. Restart Waybar

```bash
# If using Omarchy:
omarchy-restart-waybar

# Or manually:
killall waybar
waybar &
```

## Configuration

Replace placeholders in your scripts:

```bash
# Example in weather.sh
API_KEY="YOUR_OPENWEATHERMAP_API_KEY"
```

### Customizing Modules

Edit `config.jsonc` to:
- Change module order in `modules-left`, `modules-center`, `modules-right`
- Add/remove modules
- Modify format strings
- Adjust intervals

### Clock Format

Default format: `{:%a %d - %I:%M %p}`  
Shows: `Sun 05 - 09:30 AM`

Tooltip shows: `05 April 2026`

Format codes:
- `%a` - Abbreviated weekday (Sun, Mon)
- `%d` - Day of month (05)
- `%I:%M %p` - 12-hour time with AM/PM
- `%H:%M` - 24-hour time
- `%B` - Full month name

## Troubleshooting

### Waybar doesn't start

Check for JSON errors:
```bash
cat ~/.config/waybar/config.jsonc | python3 -m json.tool
```

### Missing icons

Install a Nerd Font:
```bash
# Arch
sudo pacman -S ttf-jetbrains-mono-nerd

# Or download from https://www.nerdfonts.com/
```

### Theme import error

The `style.css` imports a theme from Omarchy. If not using Omarchy, either:
1. Remove/comment the `@import` line
2. Or copy the theme file to `~/.config/omarchy/current/theme/waybar.css`

### Scripts not working

Make sure scripts are executable:
```bash
ls -la ~/.config/waybar/scripts/
```

Check script output manually:
```bash
~/.config/waybar/scripts/cpu-info.sh
```

## Credits

Based on [Omarchy](https://omarchy.org/) defaults.
