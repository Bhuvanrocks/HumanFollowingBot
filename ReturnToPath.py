import RPi.GPIO as GPIO
import cv2
import numpy as np
import mediapipe as mp
import time

# Pin Definitions
SERVO_PIN = 18
IN1_PIN = 27
IN2_PIN = 17
ENA_PIN = 9
IN3_PIN = 10
IN4_PIN = 22
ENB_PIN = 11
HALL_SENSOR_PIN = 23

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup([IN1_PIN, IN2_PIN, ENA_PIN, IN3_PIN, IN4_PIN, ENB_PIN, SERVO_PIN, HALL_SENSOR_PIN], GPIO.OUT)
GPIO.setup(HALL_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Set pull-up resistor

# Initialize PWM
pwm_servo = GPIO.PWM(SERVO_PIN, 50)  # 50Hz for servo
pwm_servo.start(0)
pwm_ena = GPIO.PWM(ENA_PIN, 1000)
pwm_enb = GPIO.PWM(ENB_PIN, 1000)
pwm_ena.start(0)
pwm_enb.start(0)

# Initialize MediaPipe Pose module
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)


# Open a log file
def start_data(filename='/home/sujith/LF2.txt'):
    try:
        with open(filename, 'w') as file:
            file.write('N\n')
    except IOError as e:
        print(f"Error opening file {filename}: {e}")


def write_data(x, filename='/home/sujith/LF2.txt'):
    try:
        with open(filename, 'a') as file:
            file.write(f'{x}\n')
    except IOError as e:
        print(f"Error writing to file {filename}: {e}")


start_data()

# Global variable for current movement direction
current_direction = "None"


def set_angle(angle):
    duty_cycle = 2 + (angle / 18)
    pwm_servo.ChangeDutyCycle(duty_cycle)
    time.sleep(0.5)
    pwm_servo.ChangeDutyCycle(0)


def detect_pose(image):
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)

    if results.pose_landmarks:
        h, w, _ = image.shape
        x_coords = [int(landmark.x * w) for landmark in results.pose_landmarks.landmark]
        y_coords = [int(landmark.y * h) for landmark in results.pose_landmarks.landmark]

        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)

        return (x_min, y_min, x_max, y_max), (x_min + x_max) // 2

    return None, None


def rotate_servo_and_detect(cap):
    frame_center_x = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) // 2
    for angle in range(10, 171, 5):
        print(f'Servo angle: {angle}')
        set_angle(angle)
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture image.")
            break

        bbox, bbox_center_x = detect_pose(frame)
        if bbox:
            x_min, y_min, x_max, y_max = bbox
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            area = x_max * y_max
            print(f'Area: {area}')
            if frame_center_x - 80 < bbox_center_x < frame_center_x + 80 and area > 5000:
                print(f"Human detected at center. Servo angle: {angle}")
                set_angle(90)  # Reset to forward position
                return angle, bbox_center_x

        cv2.imshow('Frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    set_angle(90)  # Reset servo to forward
    return None, None


def set_motor_speed(left_speed, right_speed):
    pwm_ena.ChangeDutyCycle(left_speed)
    pwm_enb.ChangeDutyCycle(right_speed)


def stop_motors():
    set_motor_speed(0, 0)
    global current_direction
    current_direction = 'S'


def set_motor_direction(left_forward, right_forward):
    GPIO.output(IN1_PIN, GPIO.HIGH if left_forward else GPIO.LOW)
    GPIO.output(IN2_PIN, GPIO.LOW if left_forward else GPIO.HIGH)
    GPIO.output(IN3_PIN, GPIO.HIGH if right_forward else GPIO.LOW)
    GPIO.output(IN4_PIN, GPIO.LOW if right_forward else GPIO.HIGH)


def move_forward(speed):
    global current_direction
    current_direction = "F"
    set_motor_direction(False, False)
    set_motor_speed(speed, speed)


def turn_left(speed):
    global current_direction
    current_direction = "L"
    set_motor_direction(False, True)
    set_motor_speed(speed, speed)


def turn_right(speed):
    global current_direction
    current_direction = "R"
    set_motor_direction(True, False)
    set_motor_speed(speed, speed)


def move_forward_for_time(speed, duration):
    move_forward(speed)
    time.sleep(duration)
    stop_motors()


def move_right_for_time(speed, duration):
    turn_right(speed)
    time.sleep(duration)
    stop_motors()


def move_left_for_time(speed, duration):
    turn_left(speed)
    time.sleep(duration)
    stop_motors()


def human_follow(cap):
    counter = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture image.")
            break

        bbox, bbox_center_x = detect_pose(frame)
        if bbox:
            frame_width = frame.shape[1]
            frame_center_x = frame_width // 2

            if bbox_center_x < frame_center_x - 80:
                print("Human is to the left. Turning left.")
                turn_left(70)
                counter += 1
            elif bbox_center_x > frame_center_x + 80:
                print("Human is to the right. Turning right.")
                turn_right(70)
                counter += 1
            else:
                print("Human is centered. Moving forward.")
                move_forward(80)
                counter += 1

            x_min, y_min, x_max, y_max = bbox
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
        else:
            stop_motors()
            print("No human detected. Stopping.")
            counter += 1
            if counter > 10:
                break

        write_data(f'{current_direction},-1')
        cv2.imshow('Frame', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


def control_motors(direction, delay):
    if delay == -1:
        delay = 0.1

    if direction == "F":
        move_forward_for_time(80, delay)
    elif direction == 'R':
        move_right_for_time(80, delay)
    elif direction == 'L':
        move_left_for_time(80, delay)
    elif direction == 'S':
        stop_motors()


def read_data(filename='/home/sujith/LF2.txt'):
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
            return [line.strip().split(',') for line in reversed(lines)]
    except IOError as e:
        print(f"Error reading file {filename}: {e}")
        return []


def return_back():
    try:
        while True:
            instructions = read_data()
            for i in instructions:
                direction = i[0]
                delay = float(i[1])
                control_motors(direction, delay)

    finally:
        pwm_ena.stop()
        pwm_enb.stop()
        pwm_servo.stop()
        GPIO.cleanup()


def main():
    if time.time() > 15:
        return_back()
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    try:
        while True:
            stop_motors()
            print("Scanning with servo...")
            detected_angle, _ = rotate_servo_and_detect(cap)

            if detected_angle is not None:
                print(f"Human detected at angle: {detected_angle}. Aligning.")
                if detected_angle < 90:
                    print("Turning right to align with human.")
                    move_right_for_time(80, 0.5)
                    write_data('R,0.5')
                else:
                    print("Turning left to align with human.")
                    move_left_for_time(80, 0.5)
                    write_data('L,0.5')

                print("Following human.")
                human_follow(cap)
            else:
                print("No human detected. Moving forward.")
                move_forward_for_time(80, 3)
                write_data('F,3')

    finally:
        cap.release()
        cv2.destroyAllWindows()
        stop_motors()
        pwm_ena.stop()
        pwm_enb.stop()
        pwm_servo.stop()
        GPIO.cleanup()


if __name__ == "__main__":
    main()
