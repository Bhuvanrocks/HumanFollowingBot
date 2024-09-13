import RPi.GPIO as GPIO
import time

# Pin Definitions
servo_pin = 18  # Servo is connected to GPIO pin 18

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(servo_pin, GPIO.OUT)

# Set up PWM for the servo on pin 18
pwm = GPIO.PWM(servo_pin, 50)  # 50Hz is a common frequency for servos
pwm.start(0)

def set_angle(angle):
    """
    Set the servo motor to the specified angle.
    The angle should be between 0 and 180 degrees.
    """
    duty_cycle = 2 + (angle / 18)  # Convert angle to duty cycle
    pwm.ChangeDutyCycle(duty_cycle)
    time.sleep(0.5)  # Give the servo time to reach the angle
    pwm.ChangeDutyCycle(0)  # Turn off the signal to prevent jitter

try:
    while True:
        angle = float(input("Enter the angle (0 to 180 degrees): "))
        if 0 <= angle <= 180:
            set_angle(angle)
        else:
            print("Please enter a valid angle between 0 and 180.")
            
except KeyboardInterrupt:
    print("Program interrupted by user.")

finally:
    pwm.stop()
    GPIO.cleanup()

