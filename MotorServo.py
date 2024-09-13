import RPi.GPIO as GPIO
import time

# Pin Definitions
SERVO_PIN = 18
IN1_PIN = 27
IN2_PIN = 17
ENA_PIN = 9
IN3_PIN = 10
IN4_PIN = 22
ENB_PIN = 11

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup([IN1_PIN, IN2_PIN, ENA_PIN, IN3_PIN, IN4_PIN, ENB_PIN, SERVO_PIN], GPIO.OUT)

# Initialize PWM
pwm_servo = GPIO.PWM(SERVO_PIN, 50)  # 50Hz for servo
pwm_servo.start(0)
pwm_ena = GPIO.PWM(ENA_PIN, 1000)
pwm_enb = GPIO.PWM(ENB_PIN, 1000)
pwm_ena.start(0)
pwm_enb.start(0)

# Global variable for current movement direction
current_direction = "None"


def set_angle(angle):
    duty_cycle = 2 + (angle / 18)
    pwm_servo.ChangeDutyCycle(duty_cycle)
    time.sleep(0.5)
    pwm_servo.ChangeDutyCycle(0)


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


def move_back(speed):
    global current_direction
    current_direction = "B"
    set_motor_direction(True, True)
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


def move_back_for_time(speed, duration):
    move_back(speed)
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


def main():
    try:
        # Example usage
        move_forward_for_time(80, 3)
        set_angle(0)
        move_back_for_time(80, 3)
        set_angle(90)
        move_right_for_time(80, 3)
        set_angle(180)
        move_left_for_time(80, 3)
        set_angle(0)  # Center the servo

    finally:
        # Cleanup
        stop_motors()
        pwm_ena.stop()
        pwm_enb.stop()
        pwm_servo.stop()
        GPIO.cleanup()


if __name__ == "__main__":
    main()
