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
- **AI Tray**: Opencode, Claude, Codex and Copilot usage modules
- **Workspaces**: Hyprland workspace integration

## Installation

### Quick install (recommended)

```bash
chmod +x install.sh
./install.sh
```

With dependencies (Arch Linux):

```bash
./install.sh --install-deps
```

### Update this repo from current ~/.config

```bash
chmod +x backup-and-update-repo.sh
./backup-and-update-repo.sh
```

This syncs by replacing existing files and adding missing ones:
- `~/.config/waybar/config.jsonc` -> `./config.jsonc`
- `~/.config/waybar/style.css` -> `./style.css`
- `~/.config/waybar/scripts/*` -> `./scripts/`
- `~/.config/waybar-ai-usage/*.example` -> `./ai-config/`

Optional (copies real tokens too):

```bash
./backup-and-update-repo.sh --include-secrets
```

### 1. Backup existing config

```bash
mv ~/.config/waybar/config.jsonc ~/.config/waybar/config.jsonc.bak
```

### 2. Copy the config

```bash
# Create scripts directory if it doesn't exist
mkdir -p ~/.config/waybar/scripts
mkdir -p ~/.config/waybar-ai-usage

# Copy all files
cp config.jsonc ~/.config/waybar/config.jsonc
cp style.css ~/.config/waybar/style.css
cp scripts/* ~/.config/waybar/scripts/
cp ai-config/*.example ~/.config/waybar-ai-usage/
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
chmod +x ~/.config/waybar/scripts/*.py
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

### AI Config

For AI modules, create and edit token files:

```bash
cp ~/.config/waybar-ai-usage/copilot.conf.example ~/.config/waybar-ai-usage/copilot.conf
cp ~/.config/waybar-ai-usage/codex.conf.example ~/.config/waybar-ai-usage/codex.conf
```

- `copilot.conf`: set `GITHUB_TOKEN=...`
- `codex.conf`: set `OPENAI_API_KEY=...` (optional, local Codex state is used first)
- `claude-usage`: uses browser cookies from Claude login session (no token file)

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
