import sys
import os
import time
import requests

# --- Platform Agnostic Keyboard Input ---
if os.name == 'nt':
    import msvcrt
else:
    import tty
    import termios
    import select

class KeyPoller:
    def __enter__(self):
        if os.name != 'nt':
            self.fd = sys.stdin.fileno()
            self.old_settings = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
        return self

    def __exit__(self, type, value, traceback):
        if os.name != 'nt':
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

    def poll(self):
        if os.name == 'nt':
            if msvcrt.kbhit():
                return msvcrt.getch()
            return None
        else:
            dr, dw, de = select.select([sys.stdin], [], [], 0)
            if not dr:
                return None
            return sys.stdin.read(1)

# --- Configuration ---
GIMBAL_URL = "http://192.168.1.146:27739/obsbot/tail/ai/gimbal"
CAMERA_URL = "http://192.168.1.146:27739/obsbot/tail/ai/camera"
FOCUS_URL = "http://192.168.1.146:80"
AI_URL = "http://192.168.1.146:27739/obsbot/tail/ai"  # AI toggle URL

PITCH_STEP = 5
YAW_STEP   = 5
ROLL_STEP  = 5
MIN_ROLL   = -133.0
MAX_ROLL   = 133.0

ZOOM_STEP  = 0.1
MIN_ZOOM   = 1.0
MAX_ZOOM   = 5.1
ZOOM_SPEED = 3

def normalize_angle(angle):
    """Normalize angle to -179 to 179 degrees."""
    while angle > 179:
        angle -= 360
    while angle < -179:
        angle += 360
    return angle

def get_ptz():
    try:
        response = requests.get(GIMBAL_URL, timeout=1)
        if response.status_code == 200:
            data = response.json()
            p = float(data.get("Degree", [0, 0, 0])[1])  # pitch
            y = float(data.get("Degree", [0, 0, 0])[2])  # yaw
            r = float(data.get("Degree", [0, 0, 0])[0])  # roll
            return (p, y, r)
        else:
            print(f"[get_ptz] Failed: {response.status_code}, {response.text}")
            return (0.0, 0.0, 0.0)
    except Exception as e:
        print(f"[get_ptz] Error: {e}")
        return (0.0, 0.0, 0.0)

def set_ptz(p, y, r):
    # Normalize yaw before sending
    y = normalize_angle(y)
    payload = {
        "cmd": "setAbsDegree",
        "rollDegree": r,
        "pitchDegree": p,
        "yawDegree": y
    }
    try:
        response = requests.post(GIMBAL_URL, json=payload, timeout=1)
        print(f"[PTZ] pitch={p:.1f}, yaw={y:.1f}, roll={r:.1f} -> {response.status_code}")
    except Exception as e:
        print(f"[PTZ] Error: {e}")

def set_zoom(ratio):
    payload = {
        "cmd": "SetZoomRatio",
        "type": 0,
        "speed": ZOOM_SPEED,
        "ratio": ratio
    }
    try:
        response = requests.post(CAMERA_URL, json=payload, timeout=1)
        print(f"[Zoom] ratio={ratio:.1f} -> {response.status_code}")
    except Exception as e:
        print(f"[Zoom] Error: {e}")

def set_focus(x=50, y=50):
    if not (0 <= x <= 100 and 0 <= y <= 100):
        print(f"[Focus] Invalid coords: x={x}, y={y} (must be 0-100)")
        return
    payload = {"msg_id": 701, "x": x, "y": y}
    try:
        response = requests.post(FOCUS_URL, json=payload, timeout=1)
        if response.status_code == 200:
            print(f"[Focus] Success: x={x}, y={y}")
        else:
            print(f"[Focus] Failed: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"[Focus] Error: {e}")

def toggle_tracking(state):
    val = 0 if state else 1  # 0 = tracking on, 1 = tracking off
    payload = {
        "cmd": "SdkSetConfig",
        "key": 3,
        "val": val
    }
    try:
        response = requests.post(AI_URL, json=payload, timeout=1)
        if response.status_code == 200:
            print(f"[Tracking] {'ON' if state else 'OFF'} -> {response.status_code}")
        else:
            print(f"[Tracking] Failed: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"[Tracking] Error: {e}")

def main():
    print("""
    Controls:
      Arrow Up/Down/Left/Right => Adjust pitch/yaw
      a / s => Roll +1 / -1
      z / x => Zoom in / out
      f     => Focus
      t     => Toggle tracking (ON/OFF)
      q     => Quit
    """)

    pitch, yaw, roll = get_ptz()
    set_ptz(pitch, yaw, roll)
    zoom_ratio = 1.0
    set_zoom(zoom_ratio)
    tracking_on = False
    toggle_tracking(tracking_on)

    with KeyPoller() as key_poller:
        while True:
            key = key_poller.poll()
            if key:
                if isinstance(key, bytes):
                    # Handle bytes from msvcrt or sys.stdin.read
                    try:
                        key_str = key.decode('utf-8')
                    except:
                        key_str = ''
                else:
                    key_str = key

                if key == b'q' or key_str == 'q':
                    print("Exiting!")
                    break
                elif key == b't' or key_str == 't':
                    tracking_on = not tracking_on
                    toggle_tracking(tracking_on)
                elif key == b'z' or key_str == 'z':
                    if zoom_ratio < MAX_ZOOM:
                        zoom_ratio += ZOOM_STEP
                        zoom_ratio = min(zoom_ratio, MAX_ZOOM)
                    set_zoom(round(zoom_ratio, 1))
                elif key == b'x' or key_str == 'x':
                    if zoom_ratio > MIN_ZOOM:
                        zoom_ratio -= ZOOM_STEP
                        zoom_ratio = max(zoom_ratio, MIN_ZOOM)
                    set_zoom(round(zoom_ratio, 1))
                elif key == b'a' or key_str == 'a':
                    if roll < MAX_ROLL:
                        roll += ROLL_STEP
                    set_ptz(round(pitch,1), round(yaw,1), round(roll,1))
                elif key == b's' or key_str == 's':
                    if roll > MIN_ROLL:
                        roll -= ROLL_STEP
                    set_ptz(round(pitch,1), round(yaw,1), round(roll,1))
                elif key == b'f' or key_str == 'f':
                    set_focus()
                
                # Arrow keys handling
                # Windows: b'\xe0' or b'\x00' followed by H, P, K, M
                # Unix: \x1b followed by [ followed by A, B, C, D
                elif os.name == 'nt' and key in (b'\x00', b'\xe0'):
                    arrow_key = msvcrt.getch()
                    if arrow_key == b'H':   # Up
                        pitch -= PITCH_STEP
                    elif arrow_key == b'P': # Down
                        pitch += PITCH_STEP
                    elif arrow_key == b'K': # Left
                        yaw -= YAW_STEP
                    elif arrow_key == b'M': # Right
                        yaw += YAW_STEP
                    set_ptz(round(pitch,1), round(yaw,1), round(roll,1))
                
                elif os.name != 'nt' and key_str == '\x1b':
                    # Read next two chars for escape sequence
                    # This is a simple blocking read for the sequence, usually fine for local terminal
                    # Ideally we'd poll, but escape sequences come fast
                    seq = sys.stdin.read(2)
                    if seq == '[A': # Up
                        pitch -= PITCH_STEP
                    elif seq == '[B': # Down
                        pitch += PITCH_STEP
                    elif seq == '[D': # Left (Note: Left is usually D, Right is C)
                        yaw -= YAW_STEP
                    elif seq == '[C': # Right
                        yaw += YAW_STEP
                    set_ptz(round(pitch,1), round(yaw,1), round(roll,1))

            time.sleep(0.05)

if __name__ == "__main__":
    main()