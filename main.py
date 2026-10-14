
import os
import time
import base64
import subprocess
from openai import OpenAI


# ============================================================
# SMART GLASSES
# ============================================================
#
# Raspberry Pi ON
#       ↓
# Program starts automatically
#       ↓
# WAIT FOR BUTTON
#       ↓
# Button pressed
#       ↓
# Capture image
#       ↓
# AI recognizes objects
#       ↓
# Ultrasonic checks distance
#       ↓
# Speaker / Vibration if needed
#       ↓
# WAIT FOR BUTTON
#
# ============================================================


# -------------------------
# SETTINGS
# -------------------------

MODEL = "gpt-5-nano-2025-08-07"

IMAGE_PATH = "/tmp/captured_image.jpg"

RESOLUTION = "640x480"


# -------------------------
# OPENAI
# -------------------------

# API key will be stored on the Raspberry Pi,
# NOT directly inside this code.

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key) if api_key else None


# ============================================================
# BUTTON
# ============================================================

def wait_for_button():
    """
    Wait until the user presses the button.

    Real Raspberry Pi GPIO code will be added
    when the button pin is finalized.
    """

    print("")
    print("[SYSTEM] Waiting for button...")

    # TODO:
    # Replace this with Raspberry Pi GPIO button input.
    #
    # Example later:
    #
    # while GPIO.input(BUTTON_PIN) == GPIO.HIGH:
    #     time.sleep(0.05)

    input("Press ENTER to simulate button press: ")

    print("[BUTTON] Button pressed!")


# ============================================================
# CAMERA
# ============================================================

def capture_image():
    """
    Take one picture when the button is pressed.
    """

    print("[CAMERA] Taking picture...")

    subprocess.run(
        [
            "fswebcam",
            "-r", RESOLUTION,
            "-S", "2",
            "--no-banner",
            IMAGE_PATH
        ],
        check=True
    )

    print("[CAMERA] Picture captured.")


# ============================================================
# CONVERT IMAGE
# ============================================================

def image_to_data_url():
    """
    Convert the picture to a format
    that can be sent to the AI.
    """

    with open(IMAGE_PATH, "rb") as image_file:

        encoded = base64.b64encode(
            image_file.read()
        ).decode("utf-8")

    return "data:image/jpeg;base64," + encoded


# ============================================================
# AI IMAGE RECOGNITION
# ============================================================

def recognize_objects():
    """
    Send the picture to the AI
    and identify the main object/obstacle.
    """

    if client is None:

        raise RuntimeError(
            "OPENAI_API_KEY is not configured."
        )

    print("[AI] Analyzing image...")

    image_data = image_to_data_url()

    prompt = (
        "You are assisting a visually impaired person. "
        "Describe the main object or obstacle directly ahead. "
        "Reply with one short sentence of no more than "
        "15 words. Do not read text."
    )

    response = client.responses.create(

        model=MODEL,

        reasoning={
            "effort": "low"
        },

        max_output_tokens=100,

        input=[
            {
                "role": "user",
                "content": [

                    {
                        "type": "input_text",
                        "text": prompt
                    },

                    {
                        "type": "input_image",
                        "image_url": image_data
                    }
                ]
            }
        ]
    )

    result = response.output_text.strip()

    print("[AI]", result)

    return result


# ============================================================
# ULTRASONIC SENSOR
# ============================================================

def get_distance():
    """
    Measure distance to the obstacle.

    GPIO code will be added when the ultrasonic
    sensor pins are finalized.
    """

    # TODO:
    # Add real ultrasonic sensor code here.

    return None


# ============================================================
# SPEAKER
# ============================================================

def speak(message):
    """
    Speak information to the user.
    """

    print("[SPEAKER]", message)

    # TODO:
    # Add text-to-speech code after
    # the speaker is connected.


# ============================================================
# VIBRATION MOTOR
# ============================================================

def vibration_on():

    print("[VIBRATION] ON")

    # TODO:
    # Add vibration motor GPIO code.


def vibration_off():

    print("[VIBRATION] OFF")

    # TODO:
    # Add vibration motor GPIO code.


# ============================================================
# FEEDBACK DECISION
# ============================================================

def provide_feedback(object_description, distance):

    print("[SYSTEM] Providing feedback...")

    # Tell the user what the camera detected.

    if object_description:

        speak(object_description)


    # No ultrasonic sensor connected yet.

    if distance is None:

        vibration_off()

        return


    print(
        "[DISTANCE]",
        round(distance, 1),
        "cm"
    )


    # --------------------------------------------------------
    # DISTANCE RULES WILL GO HERE
    # --------------------------------------------------------
    #
    # We are NOT inventing distances yet.
    #
    # Later it can look like:
    #
    # if distance <= DANGER_DISTANCE:
    #     vibration_on()
    #
    # else:
    #     vibration_off()
    #
    # --------------------------------------------------------

    vibration_off()


# ============================================================
# ONE SCAN
# ============================================================

def scan_once():
    """
    Perform ONE complete scan after
    the user presses the button.
    """

    print("")
    print("==============================")
    print("       STARTING SCAN")
    print("==============================")

    # 1. Take picture

    capture_image()


    # 2. AI recognizes object

    object_description = recognize_objects()


    # 3. Measure distance

    distance = get_distance()


    # 4. Decide feedback

    provide_feedback(
        object_description,
        distance
    )


    print("==============================")
    print("        SCAN COMPLETE")
    print("==============================")


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print("")
    print("======================================")
    print(" SMART OBSTACLE-DETECTION GLASSES")
    print("======================================")

    print("[SYSTEM] System ready.")


    while True:

        try:

            # System consumes minimal resources here
            # while waiting for user input.

            wait_for_button()


            # Button pressed:
            # camera + AI + sensors are used.

            scan_once()


            # After scan finishes, program automatically
            # returns to waiting for another button press.


        except KeyboardInterrupt:

            print("")
            print("[SYSTEM] System stopped.")

            vibration_off()

            break


        except Exception as error:

            print("")
            print("[ERROR]", error)

            vibration_off()

            print(
                "[SYSTEM] Returning to button mode..."
            )

            time.sleep(2)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
