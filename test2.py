"""Obstacle alert and camera description program for Raspberry Pi."""

import base64
import os
import subprocess
import threading
import time

import RPi.GPIO as GPIO
from gtts import gTTS
from openai import OpenAI


# Configuration
MODEL = "gpt-4o-mini"
IMAGE_PATH = "/tmp/captured_image.jpg"
RESOLUTION = "640x480"
DANGER_DISTANCE_CM = 152.4

# BCM pin numbering
BUTTON_PIN = 4
VIBRATION_PIN = 26
TRIG_PIN = 27
ECHO_PIN = 22

# Vibration output is enabled to match the user's already-tested setup.
MOTOR_ENABLED = True
VIBRATION_PULSE_SECONDS = 0.06
MIN_PULSE_INTERVAL_SECONDS = 0.12
MAX_PULSE_INTERVAL_SECONDS = 1.00
SENSOR_SAMPLE_INTERVAL_SECONDS = 0.08
DISTANCE_FILTER_SAMPLES = 3

STOP_EVENT = threading.Event()
DISTANCE_LOCK = threading.Lock()
LATEST_DISTANCE_CM = None


def get_api_key():
    """Read the API key from the OPENAI_API_KEY environment variable."""
    return os.environ.get("OPENAI_API_KEY", "").strip()


def get_distance():
    """Measure HC-SR04 distance in cm, or return None on timeout."""
    GPIO.output(TRIG_PIN, GPIO.LOW)
    time.sleep(0.000002)
    GPIO.output(TRIG_PIN, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, GPIO.LOW)

    deadline = time.monotonic() + 0.03
    while GPIO.input(ECHO_PIN) == GPIO.LOW:
        if time.monotonic() >= deadline:
            return None
    pulse_start = time.monotonic()

    deadline = time.monotonic() + 0.03
    while GPIO.input(ECHO_PIN) == GPIO.HIGH:
        if time.monotonic() >= deadline:
            return None
    pulse_end = time.monotonic()

    distance_cm = (pulse_end - pulse_start) * 34300 / 2
    # Discard implausible/out-of-range echoes instead of alarming on noise.
    if not 2 <= distance_cm <= 400:
        return None
    return distance_cm


def distance_to_pulse_interval(distance_cm):
    """Map distance to pulse spacing: closer obstacles alert more rapidly."""
    if distance_cm is None or distance_cm > DANGER_DISTANCE_CM:
        return None
    # 5 ft: about one pulse/sec; 20 cm or closer: about 8 pulses/sec.
    fraction = max(0.0, min(1.0, distance_cm / DANGER_DISTANCE_CM))
    return MIN_PULSE_INTERVAL_SECONDS + (
        MAX_PULSE_INTERVAL_SECONDS - MIN_PULSE_INTERVAL_SECONDS
    ) * fraction


def distance_monitoring_loop():
    """Pulse the vibration output increasingly quickly as an object nears."""
    print("[SYSTEM] Distance monitoring started.")
    next_pulse = 0.0
    recent = []
    while not STOP_EVENT.is_set():
        try:
            distance = get_distance()
            if distance is not None:
                recent.append(distance)
                if len(recent) > DISTANCE_FILTER_SAMPLES:
                    recent.pop(0)
                # Median rejects a single noisy ultrasonic reading.
                filtered_distance = sorted(recent)[len(recent) // 2]
            else:
                filtered_distance = None

            with DISTANCE_LOCK:
                global LATEST_DISTANCE_CM
                LATEST_DISTANCE_CM = filtered_distance
            interval = distance_to_pulse_interval(filtered_distance)

            if interval is None:
                next_pulse = 0.0
                GPIO.output(VIBRATION_PIN, GPIO.LOW)
            elif MOTOR_ENABLED and time.monotonic() >= next_pulse:
                # Short pulse, then a gap. Pulse rate rises with proximity.
                GPIO.output(VIBRATION_PIN, GPIO.HIGH)
                STOP_EVENT.wait(VIBRATION_PULSE_SECONDS)
                GPIO.output(VIBRATION_PIN, GPIO.LOW)
                next_pulse = time.monotonic() + max(
                    0.04, interval - VIBRATION_PULSE_SECONDS
                )

            if filtered_distance is not None:
                print(f"[DISTANCE] {filtered_distance:.0f} cm", end="\r")
            STOP_EVENT.wait(SENSOR_SAMPLE_INTERVAL_SECONDS)
        except Exception as exc:
            if not STOP_EVENT.is_set():
                print(f"\n[ERROR] Distance monitor: {exc}")
                STOP_EVENT.wait(0.5)


def wait_for_button_release():
    print("\n[SYSTEM] Waiting for button press...")
    while not STOP_EVENT.is_set() and GPIO.input(BUTTON_PIN) == GPIO.LOW:
        # Give the distance alert loop CPU time and avoid a busy spin.
        STOP_EVENT.wait(0.05)
    if STOP_EVENT.is_set():
        return False

    print("[BUTTON] Pressed; waiting for release.")
    while not STOP_EVENT.is_set() and GPIO.input(BUTTON_PIN) == GPIO.HIGH:
        STOP_EVENT.wait(0.05)
    if not STOP_EVENT.is_set():
        print("[BUTTON] Released; starting scan.")
        return True
    return False


def capture_image():
    print("[CAMERA] Taking picture...")
    try:
        subprocess.run(
            ["fswebcam", "-r", RESOLUTION, "-S", "2", "--no-banner", IMAGE_PATH],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
        print("[CAMERA] Picture captured.")
        return True
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"[ERROR] Camera failed: {exc}")
        return False


def speak(text):
    print(f"[SPEAKER OUT] {text}")
    try:
        audio_path = "/tmp/speech.mp3"
        gTTS(text=text, lang="en").save(audio_path)
        subprocess.run(["mpg123", "-q", audio_path], check=True, timeout=60)
    except Exception as exc:
        print(f"[ERROR] Audio failed. Check gTTS/network, mpg123, and speaker: {exc}")


def image_to_data_url():
    with open(IMAGE_PATH, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def recognize_objects(client):
    print("[AI] Analyzing image...")
    prompt = (
        "Assist a visually impaired person. Describe the main object or obstacle "
        "directly ahead in one short sentence of no more than 15 words. Do not read text."
    )
    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_to_data_url()}},
                ],
            }],
        )
        result = (response.choices[0].message.content or "").strip()
        if result:
            print(f"[AI RESULT] {result}")
            return result
    except Exception as exc:
        print(f"[ERROR] AI request failed: {exc}")
    return None


def scan_once(client):
    print("-" * 30)
    if capture_image():
        description = recognize_objects(client)
        if description:
            speak(description)
    print("-" * 30)


def main():
    api_key = get_api_key()
    client = OpenAI(api_key=api_key) if api_key else None
    if client is None:
        print("[WARNING] OPENAI_API_KEY is not set; camera descriptions are disabled.")
    if MOTOR_ENABLED:
        print("[SYSTEM] Distance-based vibration alerts enabled.")

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(VIBRATION_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(TRIG_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(ECHO_PIN, GPIO.IN)

    monitor = threading.Thread(target=distance_monitoring_loop, name="distance-monitor")
    monitor.start()

    print("\n======================================")
    print(" SMART OBSTACLE-DETECTION GLASSES")
    print("======================================")
    try:
        while not STOP_EVENT.is_set():
            if wait_for_button_release():
                if client:
                    scan_once(client)
                else:
                    print("[WARNING] Scan skipped; set OPENAI_API_KEY to enable descriptions.")
    except KeyboardInterrupt:
        print("\n[SYSTEM] Stopping.")
    finally:
        STOP_EVENT.set()
        monitor.join(timeout=2)
        GPIO.output(VIBRATION_PIN, GPIO.LOW)
        GPIO.cleanup()
        print("[SYSTEM] GPIO cleaned up. Goodbye.")


if __name__ == "__main__":
    main()
