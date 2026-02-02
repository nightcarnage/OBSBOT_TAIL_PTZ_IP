
---

````markdown
# OBSBOT Tail PTZ Keyboard Controller

A cross-platform Python script for **manual keyboard control of an OBSBOT Tail camera**, including:

- Pan / Tilt / Roll (PTZ)
- Zoom in / out
- Tap-to-focus
- AI tracking on/off
- Works on **Windows and Unix-like systems** (Linux/macOS terminals)

This is useful when you want **direct, low-latency control** without using the official app.

---

## Features

- 🎮 **Keyboard-based PTZ control**
- 🔄 **Absolute gimbal positioning**
- 🔍 **Smooth zoom control**
- 🎯 **Center focus trigger**
- 🤖 **Toggle AI tracking**
- 🧠 **Yaw angle normalization** to prevent wraparound issues
- 🖥 **Platform-agnostic keyboard polling**

---

## Controls

| Key | Action |
|----|-------|
| Arrow Up | Tilt up (pitch -) |
| Arrow Down | Tilt down (pitch +) |
| Arrow Left | Pan left (yaw -) |
| Arrow Right | Pan right (yaw +) |
| `a` | Roll + |
| `s` | Roll - |
| `z` | Zoom in |
| `x` | Zoom out |
| `f` | Focus (center of frame) |
| `t` | Toggle AI tracking ON / OFF |
| `q` | Quit |

---

## Requirements

- Python **3.7+**
- OBSBOT Tail connected on the same network
- Network access to the camera’s HTTP API

### Python Dependencies

```bash
pip install requests
````

(All other imports are from the standard library.)

---

## Configuration

At the top of the script, update the camera IP if needed:

```python
GIMBAL_URL = "http://192.168.1.146:27739/obsbot/tail/ai/gimbal"
CAMERA_URL = "http://192.168.1.146:27739/obsbot/tail/ai/camera"
FOCUS_URL  = "http://192.168.1.146:80"
AI_URL     = "http://192.168.1.146:27739/obsbot/tail/ai"
```

You can also tune:

* `PITCH_STEP`, `YAW_STEP`, `ROLL_STEP`
* `MIN_ROLL`, `MAX_ROLL`
* `ZOOM_STEP`, `MIN_ZOOM`, `MAX_ZOOM`
* `ZOOM_SPEED`

---

## How It Works

* Uses **non-blocking keyboard input**

  * `msvcrt` on Windows
  * `tty + termios + select` on Unix
* Reads current gimbal orientation on startup
* Sends **absolute PTZ commands** via HTTP POST
* Normalizes yaw to `-179° → 179°` to avoid API issues
* Runs in a tight loop with minimal latency

---

## Running the Script

```bash
python obsbot_keyboard_control.py
```

Once running, the terminal will remain active and listen for key presses until you quit with `q`.

---

## Notes & Limitations

* This script assumes **local network access** to the OBSBOT Tail API
* Focus is currently hardcoded to the **center (50, 50)** of the frame
* Escape sequence handling for arrow keys on Unix is intentionally simple
* No smoothing or acceleration curves are applied (by design)

---

## Disclaimer

This is an **unofficial control script** and is not affiliated with OBSBOT.
Use at your own risk — API behavior may change with firmware updates.

---

## License

MIT License (or adjust as needed)
