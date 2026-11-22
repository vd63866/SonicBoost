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
- 10-band graphic equalizer (31 Hz–16 kHz)
- Flat, Bass Boost, Treble Boost and Vocal presets
- PipeWire filter-chain audio processing
- Minimal dark PySide6 desktop interface

Planned features:

- Live equalizer updates without restarting PipeWire
- Compressor and limiter
- Real-time audio visualization
- Audio device selection
- Custom preset saving

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
