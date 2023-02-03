import time
from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory
factory = PiGPIOFactory()


class PROSTHETIC_HAND_GPIO:
    '''
    Initiliases 5 servos and moves them according to a dictionnary of finger 
    states (e.g {"index":"extension"})
    '''
    def __init__(self):
        # Set pin numbers for motors
        self.motor_pins = {
            "thumb": 26,
            "index": 19,
            "middle": 13,
            "ring": 6,
            "pinky": 5}

        angle = 0.45
        minPW, maxPW = (1-angle)/1000, (2+angle)/1000

        thumb_angle = 0
        thumb_minPW, thumb_maxPW = (1-thumb_angle)/1000, (2+thumb_angle)/1000

        self.motors = {finger: Servo(self.motor_pins[finger],
            min_pulse_width = thumb_minPW if finger == "thumb" else minPW,
            max_pulse_width = thumb_maxPW if finger == "thumb" else maxPW,
            pin_factory=factory) for finger in self.motor_pins}

        self.initialise_servos()

    def initialise_servos(self):
        # Start each motor at the appropriate initial position
        for finger, motor in self.motors.items():
            motor.min() if finger != "thumb" else motor.max()
        print("Initialisation of the hands ...")
        time.sleep(0.1)

    def move_motors(self, finger_states):
        '''
        Rotates fingers' servos according to their states
        :param finger_states (dict) : dictionnary that bind each finger to a
        state ("extension" or "flexion") for the current frame
        '''
        # Update duty cycle for each finger
        for finger, state in finger_states.items():
            if state == "extension":
                self.motors[finger].min() if finger != "thumb" else self.motors[finger].max()
            else :
                self.motors[finger].max() if finger != "thumb" else self.motors[finger].min()
        time.sleep(0.05)


    def cleaner(self):
        ''' Stop servos properly'''
        print("Stopping servos")
        time.sleep(0.3)
        for finger, motor in self.motors.items():
            motor.value = None
