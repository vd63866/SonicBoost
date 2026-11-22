# 🔊 SonicBoost

### Linux Audio Enhancement Application

SonicBoost is an open-source Linux desktop application
designed to provide convenient system-wide audio
control and enhancement.

Built using Python, PySide6 and PipeWire.

**Project Status:** Early Development (v0.1)

## ✨ Features

Currently implemented:

- System-wide master volume control
- Software volume amplification up to 125%
- Mute and unmute controls
- Reset volume to 100%
- Automatic volume status refresh
- Minimal dark desktop interface

Planned features:

- 10-band graphic equalizer
- Bass and treble enhancement
- Audio presets
- Compressor and limiter
- Real-time audio visualization
- Audio device selection

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| PySide6 | Desktop interface |
| PipeWire | Linux audio infrastructure |
| WirePlumber | Audio session management |
| wpctl | Audio volume control |

## 💻 Requirements

- Linux distribution
- Python 3
- PySide6
- PipeWire
- WirePlumber

## 📦 Installation

### 1. Install dependencies

On Arch Linux / Manjaro:

```bash
sudo pacman -S --needed \
    python \
    pyside6 \
    pipewire \
    pipewire-pulse \
    wireplumber
