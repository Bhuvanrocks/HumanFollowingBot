import RPi.GPIO as GPIO
import time
import cv2
import numpy as np
import serial

# Pin Definitions
in1_pin = 27  # Motor 1 IN1
in2_pin = 17  # Motor 1 IN2
ena_pin = 9   # Motor 1 Enable
in3_pin = 10  # Motor 2 IN3
in4_pin = 22  # Motor 2 IN4
enb_pin = 11  # Motor 2 Enable

# Setup
GPIO.setmode(GPIO.BCM)  # Use Broadcom pin numbering
GPIO.setup(in1_pin, GPIO.OUT)
GPIO.setup(in2_pin, GPIO.OUT)
GPIO.setup(ena_pin, GPIO.OUT)
GPIO.setup(in3_pin, GPIO.OUT)
GPIO.setup(in4_pin, GPIO.OUT)
GPIO.setup(enb_pin, GPIO.OUT)

# Initialize PWM on Enable pins
pwm_ena = GPIO.PWM(ena_pin, 1000)  # Set frequency to 1 kHz
pwm_enb = GPIO.PWM(enb_pin, 1000)  # Set frequency to 1 kHz
pwm_ena.start(0)  # Start PWM with 0% duty cycle
pwm_enb.start(0)  # Start PWM with 0% duty cycle


def set_motor_direction(left_motor_forward, right_motor_forward, speed):
    """Control both motors."""
    GPIO.output(in1_pin, GPIO.HIGH if left_motor_forward else GPIO.LOW)
    GPIO.output(in2_pin, GPIO.LOW if left_motor_forward else GPIO.HIGH)
    GPIO.output(in3_pin, GPIO.HIGH if right_motor_forward else GPIO.LOW)
    GPIO.output(in4_pin, GPIO.LOW if right_motor_forward else GPIO.HIGH)
    pwm_ena.ChangeDutyCycle(speed)
    pwm_enb.ChangeDutyCycle(speed)


def detect_color(image, lower_color, upper_color, frame_center_x):
    image = cv2.flip(image, 1)
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_image, lower_color, upper_color)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    result_image = image.copy()

    if contours:
        # Find the largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        area=cv2.contourArea(largest_contour)
        if area > 500:
            x, y, w, h = cv2.boundingRect(largest_contour)
            bbox_center_x = x + w // 2
            # Determine direction based on object position
            if area<5000:
                if bbox_center_x < frame_center_x - 50:
                    # Object is on the left side
                    set_motor_direction(True, False, 85)  # Move left
                    print("Moving Left")
                elif bbox_center_x > frame_center_x + 50:
                    # Object is on the right side
                    set_motor_direction(False, True, 85)  # Move right
                    print("Moving Right")
                else:
                    set_motor_direction(False, False, 85)  # forward
                    print('Going forward')
            elif area>80000:
                set_motor_direction(True, True, 85)  # Backward
                print("Going backward")
            else:
                if bbox_center_x < frame_center_x - 50:
                    # Object is on the left side
                    set_motor_direction(True, False, 85)  # Move left
                    print("Moving Left")
                elif bbox_center_x > frame_center_x + 50:
                    # Object is on the right side
                    set_motor_direction(False, True, 85)  # Move right
                    print("Moving Right")
                else :   
                    set_motor_direction(True,True,0)
                    print('Stopped')


            cv2.rectangle(result_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(result_image, f'Center: {bbox_center_x}', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    return result_image


def main():
    cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    lower_green = np.array([35, 100, 100])
    upper_green = np.array([85, 255, 255])

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture image.")
                break

            frame_height, frame_width = frame.shape[:2]
            frame_center_x = frame_width // 2

            result_frame = detect_color(frame, lower_green, upper_green, frame_center_x)

            cv2.imshow('Detected Color with Distances', result_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        # Stop the motors and cleanup GPIO
        set_motor_direction(True, True, 0)
        pwm_ena.stop()
        pwm_enb.stop()
        GPIO.cleanup()


if _name_ == "_main_":
    main()
