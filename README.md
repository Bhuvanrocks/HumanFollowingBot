#Human Following Robot Using Raspberry Pi, OpenCV, and MediaPipe
This project implements a human-following robot using a Raspberry Pi, motor control, and real-time pose detection through MediaPipe and OpenCV. The robot is equipped with two DC motors controlled via GPIO pins on the Raspberry Pi. By detecting human pose landmarks from video input, the robot adjusts its movement to follow the detected person.

Features:
Real-time human detection: Uses MediaPipe's Pose module to detect and track a human's pose landmarks in real-time.
Motor control: Controls two DC motors for forward, backward, and turning movements.
Bounding box detection: Calculates the center of the detected human pose and moves the robot accordingly.
Direction adjustments: The robot turns left, right, or moves forward based on the position of the person relative to the center of the video frame.
Failsafe: Stops the motors when no human is detected or when the robot is misaligned.
Hardware Requirements:
Raspberry Pi (any version with GPIO support)
Webcam or Pi Camera
L298N Motor Driver or equivalent
2 DC motors with wheels
Power supply (suitable for motors and Pi)
Jumper wires for GPIO connections
Software Requirements:
Python 3.x
OpenCV
MediaPipe
RPi.GPIO
How It Works:
The Raspberry Pi captures video input using OpenCV.
The MediaPipe library detects the pose landmarks of a person in the frame.
Based on the detected pose, a bounding box is drawn around the person.
The robot calculates the relative position of the person and moves accordingly:
Turn Left if the person is on the left of the frame.
Turn Right if the person is on the right of the frame.
Move Forward if the person is in the center of the frame.
Stop if no person is detected.
Getting Started:
Clone this repository and follow the instructions to set up the hardware and install the required libraries. Once everything is set up, run the provided Python script to start the human-following robot.

This description gives a clear overview of the project and how it works. You can adjust the details as per your exact project setup.
