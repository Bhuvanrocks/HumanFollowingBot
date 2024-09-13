import RPi.GPIO as GPIO
import cv2
import numpy as np
import mediapipe as mp
import time

# Pin Definitions
in1_pin = 27  # Motor 1 IN1
in2_pin = 17  # Motor 1 IN2
ena_pin = 9   # Motor 1 Enable
in3_pin = 10  # Motor 2 IN3
in4_pin = 22  # Motor 2 IN4
enb_pin = 11  # Motor 2 Enable

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(in1_pin, GPIO.OUT)
GPIO.setup(in2_pin, GPIO.OUT)
GPIO.setup(ena_pin, GPIO.OUT)
GPIO.setup(in3_pin, GPIO.OUT)
GPIO.setup(in4_pin, GPIO.OUT)
GPIO.setup(enb_pin, GPIO.OUT)

# Initialize PWM
pwm_ena = GPIO.PWM(ena_pin, 1000)
pwm_enb = GPIO.PWM(enb_pin, 1000)
pwm_ena.start(0)
pwm_enb.start(0)

def set_motor_speed(left_speed, right_speed):
    pwm_ena.ChangeDutyCycle(left_speed)
    pwm_enb.ChangeDutyCycle(right_speed)

def stop_motors():
    set_motor_speed(0, 0)

def set_motor_direction(left_motor_forward, right_motor_forward):
    GPIO.output(in1_pin, GPIO.HIGH if left_motor_forward else GPIO.LOW)
    GPIO.output(in2_pin, GPIO.LOW if left_motor_forward else GPIO.HIGH)
    GPIO.output(in3_pin, GPIO.HIGH if right_motor_forward else GPIO.LOW)
    GPIO.output(in4_pin, GPIO.LOW if right_motor_forward else GPIO.HIGH)

def turn_left(speed):
    set_motor_direction(False, True)
    set_motor_speed(0, speed)

def turn_right(speed):
    set_motor_direction(True, False)
    set_motor_speed(speed, 0)

def move_forward(speed):
    set_motor_direction(False, False)
    set_motor_speed(speed, speed)

def move_backward(speed):
    set_motor_direction(True, True)
    set_motor_speed(speed, speed)

# Initialize MediaPipe Pose module
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

def detect_pose(image):
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)

    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            image,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS
        )
        landmarks = results.pose_landmarks.landmark
        h, w, _ = image.shape
        x_coords = [int(landmark.x * w) for landmark in landmarks]
        y_coords = [int(landmark.y * h) for landmark in landmarks]

        x_min = min(x_coords)
        x_max = max(x_coords)
        y_min = min(y_coords)
        y_max = max(y_coords)

        return (x_min, y_min, x_max, y_max), (x_min + x_max) // 2

    return None, None

def main():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture image.")
                break

            bbox, bbox_center_x = detect_pose(frame)

            frame_height, frame_width = frame.shape[:2]
            frame_center_x = frame_width // 2

            if bbox:
                # Draw bounding box
                x_min, y_min, x_max, y_max = bbox
                cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                cv2.putText(frame, f'Center: {bbox_center_x}', (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                # Control robot movement based on bounding box position
                if bbox_center_x < frame_center_x - 80:
                    turn_left(40)
                    print("Turning Left")
                elif bbox_center_x > frame_center_x + 80:
                    turn_right(40)
                    print("Turning Right")
                else:
                    move_forward(60)
                    print("Moving Forward")

            else:
                stop_motors()
                print("Stopped")

            cv2.imshow('Pose Detection with Bounding Box', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        stop_motors()
        pwm_ena.stop()
        pwm_enb.stop()
        GPIO.cleanup()

if __name__ == "__main__":
    main()
