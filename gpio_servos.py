import RPi.GPIO as GPIO
import time


class PROSTHETIC_HAND_GPIO:
    '''
    Initiliases 5 servos and moves them according to a dictionnary of finger 
    states (e.g {"index":"extension"})
    '''
    def __init__(self):
        
        # Set GPIO numbering mode
        GPIO.setmode(GPIO.BOARD)

        # Set pin numbers for motors
        self.motor_pins = {
            "thumb": 37,
            "index": 35,
            "middle": 33,
            "ring": 31,
            "pinky": 29}

        # Set up motor pins as outputs
        for finger, pin in self.motor_pins.items():
            GPIO.setup(pin, GPIO.OUT)

        # Create PWM objects for each motor
        self.motors = {finger: GPIO.PWM(self.motor_pins[finger], 50) for finger in list(self.motor_pins.keys())}

        # Initialize servo duty cycles for each finger state
        self.thumb_duty = {'extension': 5, 'flexion': 1}
        self.other_fingers_duty = {'extension': 2, 'flexion': 12}
        
        self.initialise_servos()
        time.sleep(0.3)

    def initialise_servos(self):
        # Start each motor at the appropriate initial position
        for finger, motor in self.motors.items():
            if finger == "thumb":
                motor.start(self.thumb_duty["extension"])
            else:
                motor.start(self.other_fingers_duty["extension"])

    def move_motors(self, finger_states):
        '''
        Rotates fingers' servos according to their states
        :param finger_states (dict) : dictionnary that bind each finger to a
        state ("extension" or "flexion") for the current frame
        '''
        # Update duty cycle for each finger
        for finger, state in finger_states.items():
            if finger == "thumb":
                self.motors["thumb"].ChangeDutyCycle(self.thumb_duty[state])
            else:
                self.motors[finger].ChangeDutyCycle(self.other_fingers_duty[state])


    def cleaner(self):
        ''' Stop servos properly'''
        print("Stopping servos")
        self.initialise_servos()
        time.sleep(0.3)
        self.motors["thumb"].stop()
        for finger, motor in self.motors.items():
            motor.stop()
        GPIO.cleanup()
