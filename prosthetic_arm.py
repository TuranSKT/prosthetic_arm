import RPi.GPIO as GPIO
import time
import argparse

def move(fingers_to_move, wait):
    # Set GPIO numbering mode
    GPIO.setmode(GPIO.BOARD)

    # Set pin numbers for motors
    motor_pins = {
        "thumb": 11,
        "index": 13,
        "middle": 15,
        "ring": 12,
        "pinky": 16
    }

    # Set up motor pins as outputs
    for finger in fingers_to_move:
        GPIO.setup(motor_pins[finger], GPIO.OUT)

    # Create PWM objects for each motor
    motors = {finger: GPIO.PWM(motor_pins[finger], 50) for finger in fingers_to_move}

    # Set initial positions for each motor
    initial_positions = {
        "thumb": 5,
        "index": 2,
        "middle": 2,
        "ring": 2,
        "pinky": 2
    }

    # Start each motor at the appropriate initial position
    for finger, motor in motors.items():
        motor.start(initial_positions[finger])
    time.sleep(1)

    # Change duty cycle of each motor to the appropriate value
    for finger, motor in motors.items():
        if finger == "thumb":
            motor.ChangeDutyCycle(1)
        else:
            motor.ChangeDutyCycle(12)
    time.sleep(wait)

    # Return duty cycle of each motor to the appropriate initial position
    for finger, motor in motors.items():
        motor.ChangeDutyCycle(initial_positions[finger])
    time.sleep(1)

    # Stop each motor and clean up GPIO
    for motor in motors.values():
        motor.stop()
    GPIO.cleanup()

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Move specified fingers.")
    parser.add_argument("fingers", nargs="+", choices=["thumb", "index", "middle", "ring", "pinky", "full"], help="fingers to move")
    parser.add_argument("--wait", type=int, default=1, help="number of seconds to wait after ChangeDutyCycle")
    args = parser.parse_args()

    # If "full" is specified, move all fingers
    if "full" in args.fingers:
        fingers_to_move = ["thumb", "index", "middle", "ring", "pinky"]
    else:
        fingers_to_move = args.fingers

    # Move specified fingers
    move(fingers_to_move, args.wait)
