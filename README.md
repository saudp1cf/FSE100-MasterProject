# FSE 100 Master Project — Smart Obstacle-Detection Glasses

**Team:** Group 7  
**Course:** FSE 100  
**Progress report date:** October 14, 2026

## Project Overview

Our team is developing a wearable smart-glasses prototype to help people with visual impairments detect obstacles around head and upper-body level. A traditional white cane is valuable for mobility, but it may not detect hazards such as open cabinet doors, low branches, signs, and objects protruding into a walking path.

The proposed system combines camera-based AI object recognition with ultrasonic distance measurement. It is designed to provide feedback through audio and vibration so users can receive information about nearby obstacles without relying on sound alone.

> **Project status:** This is a work in progress. The features and hardware described below are the intended design; not all components have been integrated or fully tested yet.

## Objectives

- Detect and identify objects in front of the user using a camera and AI-based image recognition.
- Measure the distance to nearby obstacles using an ultrasonic sensor.
- Provide audio feedback describing detected objects.
- Use vibration alerts to warn when an obstacle is too close.
- Keep the wearable components lightweight, comfortable, and practical to use.
- Develop and test an affordable prototype within the project’s time and budget constraints.

## Planned Hardware

| Component | Purpose |
| --- | --- |
| Raspberry Pi | Runs the processing and control software |
| Camera | Captures images for object recognition |
| Ultrasonic sensor | Measures distance to nearby obstacles |
| Speaker | Provides spoken or other audio alerts |
| Vibration motor | Provides tactile proximity warnings |
| Battery / portable case | Powers the system while keeping heavier components off the glasses |

The current design places the camera and ultrasonic sensor at the front of the glasses. The Raspberry Pi and battery may be carried in a separate pouch or case to reduce weight on the frame.

## Planned Software and System Behavior

The intended processing flow is:

1. Capture images from the camera.
2. Run AI-based object recognition on the image data.
3. Read distance measurements from the ultrasonic sensor.
4. Use the recognition and distance information to determine whether an obstacle warning is needed.
5. Alert the user through audio feedback and/or the vibration motor.
6. Continue scanning the environment.

The exact AI model, software libraries, pin assignments, and launch commands should be documented here once they are finalized in the implementation.

## Development Progress

As of **October 14, 2026**, the progress report records the following:

- Software setup: **100%**
- AI image recognition: **100%**
- Camera software setup: **100%**
- AI object-detection testing: **100%**

The next planned tasks include ultrasonic sensor programming, obstacle-detection logic, camera/AI integration, system-processing integration, vibration and speaker feedback, hardware setup, prototype assembly, and full-system testing. These tasks are not marked complete in the current progress report.

## Repository Contents

This GitHub repository is currently intended as the **project documentation repository** for FSE 100 Master Project Group 7. Use it to keep project documents and implementation notes together.

Suggested organization as the project develops:

```text
FSE100-MasterProject/
├── README.md
├── docs/
│   ├── project-charter.md
│   ├── design-and-requirements.md
│   └── progress-reports/
└── src/
    ├── camera/
    ├── object_detection/
    ├── ultrasonic_sensor/
    └── feedback/
```

This is a suggested structure, not a description of files that are already present. Add folders only when the corresponding materials or code are committed.

## Setup and Usage

The repository currently serves as documentation, and a reproducible software setup is not yet specified. Once the implementation is committed, update this section with:

- Raspberry Pi model and operating-system version
- Required Python version and dependencies
- AI model and model-weight setup instructions
- Camera and ultrasonic sensor wiring / GPIO assignments
- Configuration values and environment variables
- Commands to start the application
- Steps to run individual component tests and the integrated system

Do not commit passwords, access tokens, private keys, or other secrets.

## Testing Plan

Planned validation should include:

1. **Camera test:** Confirm that the camera captures usable images.
2. **Object-recognition test:** Check whether the AI identifies selected objects reliably.
3. **Distance-sensor test:** Compare ultrasonic readings against known distances.
4. **Vibration test:** Confirm that the motor activates at the intended warning threshold.
5. **Audio test:** Confirm that audio feedback is clear and timely.
6. **Integration test:** Verify that camera recognition, distance readings, and alerts work together.
7. **Wearability test:** Check comfort, stability, and component weight during normal movement.

Testing should be conducted in a controlled environment. This prototype is intended to supplement existing mobility tools, not replace a white cane, guide dog, or other established mobility aid.

## Team

- Mert Alp Altay
- Kevin Kamble
- Faris Shaheen
- Saud Alghanim
- Abdullah Al Memari

