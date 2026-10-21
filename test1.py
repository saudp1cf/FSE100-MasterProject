import os
import time
import base64
import subprocess
import threading
from openai import OpenAI
import RPi.GPIO as GPIO
from gtts import gTTS

# ============================================================
# CONFIGURATION & PINS
# ============================================================

# 1. Hardcode your API key here
API_KEY = ""

MODEL = "gpt-4o-mini"
IMAGE_PATH = "/tmp/captured_image.jpg"
RESOLUTION = "640x480"
DANGER_DISTANCE_CM = 152.4  # 5 feet = 152.4 cm

# GPIO Pins (BCM Mode)
BUTTON_PIN = 4       # 3V Button
VIBRATION_PIN = 26   # Vibration Motor
TRIG_PIN = 27        # Ultrasonic TRIG
ECHO_PIN = 22        # Ultrasonic ECHO

# Hardware Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(VIBRATION_PIN, GPIO.OUT)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

# Initialize OpenAI
client = OpenAI(api_key=API_KEY) if API_KEY != "YOUR_API_KEY_HERE" else None

# ============================================================
# CONSTANT ULTRASONIC SENSOR (BACKGROUND THREAD)
# ============================================================

def get_distance():
    """Measures distance once using HC-SR04"""
    # Send 10 microsecond pulse to TRIG
    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, False)

    start_time = time.time()
    stop_time = time.time()

    # Save start time
    timeout = time.time()
    while GPIO.input(ECHO_PIN) == 0:
        start_time = time.time()
        if time.time() - timeout > 0.1: # Timeout to prevent freezing
            return None

    # Save time of arrival
    timeout = time.time()
    while GPIO.input(ECHO_PIN) == 1:
        stop_time = time.time()
        if time.time() - timeout > 0.1:
            return None

    # Calculate distance (Speed of sound = 34300 cm/s)
    elapsed = stop_time - start_time
    distance_cm = (elapsed * 34300) / 2
    return distance_cm

def distance_monitoring_loop():
    """Runs constantly in the background to check 5ft threshold."""
    print("[SYSTEM] Ultrasonic background monitoring started (5ft limit).")
    while True:
        dist = get_distance()
        
        if dist is not None and dist <= DANGER_DISTANCE_CM:
            GPIO.output(VIBRATION_PIN, GPIO.HIGH)
        else:
            GPIO.output(VIBRATION_PIN, GPIO.LOW)
            
        time.sleep(0.1) # Check 10 times a second

# Start the background distance monitor immediately
monitor_thread = threading.Thread(target=distance_monitoring_loop, daemon=True)
monitor_thread.start()


# ============================================================
# BUTTON & HARDWARE
# ============================================================

def wait_for_button_release():
    """Waits for the user to press AND release the button."""
    print("\n[SYSTEM] Waiting for button press...")
    
    # 1. Wait for press (LOW to HIGH)
    while GPIO.input(BUTTON_PIN) == GPIO.LOW:
        time.sleep(0.05)
        
    print("[BUTTON] Pressed... waiting for release.")
    
    # 2. Wait for release (HIGH to LOW)
    while GPIO.input(BUTTON_PIN) == GPIO.HIGH:
        time.sleep(0.05)
        
    print("[BUTTON] Released! Triggering scan.")

def capture_image():
    """Captures a photo via USB Camera."""
    print("[CAMERA] Taking picture...")
    try:
        subprocess.run(
            ["fswebcam", "-r", RESOLUTION, "-S", "2", "--no-banner", IMAGE_PATH],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        print("[CAMERA] Picture captured.")
        return True
    except Exception as e:
        print(f"[DEBUG ERROR] Camera failed: {e}")
        return False


# ============================================================
# AI & AUDIO
# ============================================================

def speak(text):
    """Converts text to speech and plays it via Bluetooth speaker."""
    print(f"[SPEAKER OUT] {text}")
    try:
        # Create speech audio file
        tts = gTTS(text=text, lang='en')
        tts.save("/tmp/speech.mp3")
        
        # Play audio file using mpg123
        os.system("mpg123 -q /tmp/speech.mp3")
    except Exception as e:
        print(f"[DEBUG ERROR] Audio failed. Is Bluetooth speaker connected? Error: {e}")

def image_to_base64():
    with open(IMAGE_PATH, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"

def recognize_objects():
    """Sends image to AI."""
    if not client:
        print("[DEBUG ERROR] Please replace 'YOUR_API_KEY_HERE' with your real API key.")
        return None

    print("[AI] Analyzing image...")
    image_data = image_to_base64()
    prompt = "You are assisting a visually impaired person. Describe the main object or obstacle directly ahead in one short sentence of no more than 15 words. Do not read text."

    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=150,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_data}}
                    ]
                }
            ]
        )
        result = response.choices[0].message.content.strip()
        print(f"[AI RESULT] {result}")
        return result
    except Exception as e:
        print(f"[DEBUG ERROR] AI Request Failed: {e}")
        return None


# ============================================================
# MAIN EXECUTION
# ============================================================

def scan_once():
    """Runs one camera and AI cycle."""
    print("-" * 30)
    
    if capture_image():
        description = recognize_objects()
        if description:
            speak(description)
            
    print("-" * 30)

def main():
    print("\n======================================")
    print(" SMART OBSTACLE-DETECTION GLASSES")
    print("======================================")
    
    try:
        while True:
            # Main thread waits for button and handles AI
            # (Vibration/Distance is handled automatically in the background thread)
            wait_for_button_release()
            scan_once()

    except KeyboardInterrupt:
        print("\n[SYSTEM] System stopped by user.")
    finally:
        GPIO.cleanup()
        print("[SYSTEM] Hardware pins cleaned up. Goodbye.")

if __name__ == "__main__":
    main()