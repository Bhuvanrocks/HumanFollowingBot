import RPi.GPIO as GPIO
import cv2
import mediapipe as mp
import time
from gpiozero import DistanceSensor
from pydub import AudioSegment
import simpleaudio as sa

# Load and prepare audio for playback
audio = AudioSegment.from_file("/home/sujith/Downloads/WhatsApp Audio 2024-08-21 at 10.34.15 PM.mpeg")


def play_audio():
    try:
        print("Button pressed, playing audio...")
        play_obj = sa.play_buffer(audio.raw_data, num_channels=audio.channels, bytes_per_sample=audio.sample_width,
                                  sample_rate=audio.frame_rate)
        play_obj.wait_done()
    except Exception as e:
        print(f"Error playing audio: {e}")


# Pin Definitions
servo_pin = 13
in1_pin = 27
in2_pin = 17
ena_pin = 9
in3_pin = 10
in4_pin = 22
enb_pin = 11
hall_sensor_pin = 23
TRIG_PIN = 21
ECHO_PIN = 20

sensor = DistanceSensor(echo=ECHO_PIN, trigger=TRIG_PIN)

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup([in1_pin, in2_pin, ena_pin, in3_pin, in4_pin, enb_pin, servo_pin, hall_sensor_pin], GPIO.OUT)
GPIO.setup(hall_sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Initialize PWM
pwm = GPIO.PWM(servo_pin, 50)
pwm.start(0)
pwm_ena = GPIO.PWM(ena_pin, 1000)
pwm_enb = GPIO.PWM(enb_pin, 1000)
pwm_ena.start(0)
pwm_enb.start(0)

# Initialize MediaPipe Pose module
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

current_direction = "None"
human_detected = False
file_path = '/home/sujith/LF3.txt'


def start_file():
    try:
        with open(file_path, 'w') as file:
            file.write('N\n\n')
    except IOError as e:
        print(f"Error opening file {file_path}: {e}")


start_file()


def write_data(x):
    try:
        with open(file_path, 'a') as file:
            file.write(x)
    except IOError as e:
        print(f"Error writing to file {file_path}: {e}")


def get_distance():
    dis = round(sensor.distance * 100, 2)
    print('Distance', dis)
    return dis


def set_angle(angle):
    duty_cycle = 2 + (angle / 18)
    pwm.ChangeDutyCycle(duty_cycle)
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)


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
        print('Servo angle:', angle)
        set_angle(angle)
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture image.")
            break
        bbox, bbox_center_x = detect_pose(frame)
        if bbox:
            x_min, y_min, x_max, y_max = bbox
            area = x_max * y_max
            print('Area', area)
            if frame_center_x - 100 < bbox_center_x < frame_center_x + 100 and area > 5000:
                print(f"Human detected at center. Servo angle: {angle}")
                set_angle(90)
                return angle, bbox_center_x
        cv2.imshow('Frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    set_angle(90)
    return None, None


def set_motor_speed(left_speed, right_speed):
    pwm_ena.ChangeDutyCycle(left_speed)
    pwm_enb.ChangeDutyCycle(right_speed)


def stop_motors():
    global current_direction
    current_direction = 'S'
    set_motor_speed(0, 0)


def set_motor_direction(left_forward, right_forward):
    GPIO.output(in1_pin, GPIO.HIGH if left_forward else GPIO.LOW)
    GPIO.output(in2_pin, GPIO.LOW if left_forward else GPIO.HIGH)
    GPIO.output(in3_pin, GPIO.HIGH if right_forward else GPIO.LOW)
    GPIO.output(in4_pin, GPIO.LOW if right_forward else GPIO.HIGH)


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


def move_forward_for_steps(speed, steps):
    move_forward(speed)
    step = 0
    while step <= steps:
        if GPIO.input(hall_sensor_pin) == GPIO.LOW:
            step += 1
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
    global human_detected
    counter = 0
    moves = 0
    while True and not human_detected:
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
                turn_left(40)
                moves += 1
            elif bbox_center_x > frame_center_x + 80:
                print("Human is to the right. Turning right.")
                turn_right(40)
                moves += 1
            else:
                print("Human is centered. Moving forward.")
                move_forward(60)
                moves += 1
            x_min, y_min, x_max, y_max = bbox
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
        else:
            stop_motors()
            counter += 1
            print("No human detected. Stopping.")
            if moves > 5:
                human_detected = True
                play_audio()
                break

            if counter > 10:
                break
        cv2.imshow('Frame', frame)
        write_data(f'{current_direction},0.2')
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return
    try:
        while True and not human_detected:
            stop_motors()
            print("Scanning with servo...")
            detected_angle, _ = rotate_servo_and_detect(cap)
            if detected_angle is not None:
                print(f"Human detected at angle: {detected_angle}. Aligning.")
                if 0 < detected_angle < 70:
                    print("Turning left to align with human.")
                    move_left_for_time(60, 1)
                    write_data('L,1')
                elif 110 < detected_angle < 180:
                    print("Turning right to align with human.")
                    move_right_for_time(60, 1)
                    write_data('R,1')
                else:
                    move_forward_for_time(60, 2)
                    print('Moving forward to align with human')
                    write_data('F,2')
                print("Following human.")
                human_follow(cap)
            else:
                print("No human detected. Moving forward.")
                move_forward_for_steps(60, 3)
                write_data('F,3')
    finally:
        cap.release()
        cv2.destroyAllWindows()
        stop_motors()
        pwm_ena.stop()
        pwm_enb.stop()
        pwm.stop()
        GPIO.cleanup()


if _name_ == "_main_":
    main()
