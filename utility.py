"""Common utilities."""
import xml.etree.ElementTree as ET
import numpy as np
import math
import RPi.GPIO as GPIO
import time
import argparse

class PROSTHETIC_HAND_GPIO:
    def __init__(self):
        # Set GPIO numbering mode
        GPIO.setmode(GPIO.BOARD)

        # Set pin numbers for motors
        self.motor_pins = {
            "thumb": 11,
            "index": 13,
            "middle": 15,
            "ring": 12,
            "pinky": 16}

        # Set up motor pins as outputs
        for finger, pin in self.motor_pins.items():
            GPIO.setup(pin, GPIO.OUT)

        # Create PWM objects for each motor
        self.motors = {finger: GPIO.PWM(self.motor_pins[finger], 50) for finger in list(self.motor_pins.keys())}

        # Initialize servo duty cycles for each finger state
        self.thumb_duty_cycles = {'extension': 5, 'mid': 3, 'flexion': 1}
        self.other_fingers_duty_cycles = {'extension': 2, 'mid': 10, 'flexion': 12}
        
        # Start each motor at the appropriate initial position
        for finger, motor in self.motors.items():
            if finger == "thumb":
                motor.start(self.thumb_duty_cycles["extension"])
            else:
                motor.start(self.other_fingers_duty_cycles["extension"])
        time.sleep(0.3)

    def move_motors(self, finger_states):
        # Update duty cycle for each finger
        for finger, state in finger_states.items():
            if finger == "thumb":
                self.motors["thumb"].ChangeDutyCycle(self.thumb_duty_cycles[state])
            else:
                self.motors[finger].ChangeDutyCycle(self.other_fingers_duty_cycles[state])
        # Cleanup
        #self.motors["thumb"].stop()
        #for finger, motor in self.motors.items():
        #    motor.stop()
        #GPIO.cleanup()

def flip_array(target_array):
  # Flip horizontally a given array
  return np.array([row[::-1] for row in target_array])

def process_landmarks(landmarks, image_height, image_width):
    """
    Converts a list of landmarks into a list of lists of coordinates.
    :param landmarks (List[landmark]): A list of landmarks to be converted.
    :param image_height (int): Height of the image.
    :param image_width (int): Width of the image.
    :return: A list of lists containing the x, y, z coordinates of each landmark in the given image.
    """
    processed_landmarks = []
    for landmark in landmarks[0].landmark:
        processed_landmarks.append([landmark.x*image_width, 
                            landmark.y*image_height, 
                            landmark.z])
    return processed_landmarks

def get_angles(finger_landmarks):
    # Define vectors between the first and second landmarks and the last and second landmarks
    v1 = [finger_landmarks[1][0]-finger_landmarks[0][0], finger_landmarks[1][1]-finger_landmarks[0][1], finger_landmarks[1][2]-finger_landmarks[0][2]]
    v2 = [finger_landmarks[2][0]-finger_landmarks[1][0], finger_landmarks[2][1]-finger_landmarks[1][1], finger_landmarks[2][2]-finger_landmarks[1][2]]
    # Calculate the dot product and magnitude of the vectors
    dot = v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]
    mag1 = math.sqrt(v1[0]**2 + v1[1]**2 + v1[2]**2)
    mag2 = math.sqrt(v2[0]**2 + v2[1]**2 + v2[2]**2)
    # Calculate the angle between the vectors
    angle = math.acos(dot/(mag1*mag2))
    return angle

def determine_state(angles, min_angle, max_angle):
    print(angles, min_angle, max_angle)
    if angles > max_angle:
        return "flexion"
    elif angles < min_angle:
        return "extension"
    else:
        return "mid"

def state_detector(landmarks, min_angle, max_angle):
    fingers = ["thumb", "index", "middle", "ring", "pinky"]
    states = {}
    # Iterate through each finger
    for i in range(1, 21, 4):
        # Get the landmarks for the current finger
        finger_landmarks = landmarks[i:i+4]
        # Get the angles between the landmarks
        angles = get_angles(finger_landmarks)
        # Determine the state of the finger based on the angles
        #print(fingers[i//4])
        if i//4:
            states[fingers[i//4]] = determine_state(angles, min_angle, max_angle)
        else:
            states[fingers[i//4]] = determine_state(angles, 0.05, 0.1)
    return states

class SVG:
    def __init__(self, landmarks_dict, connections_dict, src_size):
        self.landmarks_dict = landmarks_dict
        self.connections_dict = connections_dict
        self.src_size = src_size
        
    def create_svg(self):
        #Create the root element
        svg_root = ET.Element("svg", width=str(self.src_size[0]), height=str(self.src_size[1]))

        # Add a circle element for each point in the dictionary
        for landmark, coords in self.landmarks_dict.items():
            ET.SubElement(svg_root, "circle", cx=str(coords[0]), cy=str(coords[1]), r="2")

        # Add a line element for each line in the dictionary
        for connection, lines in self.connections_dict.items():
            for line in lines:
                p1 = self.landmarks_dict[str(line[0])]
                p2 = self.landmarks_dict[str(line[1])]
                ET.SubElement(svg_root, "line", x1=str(p1[0]), y1=str(p1[1]), x2=str(p2[0]), y2=str(p2[1]), stroke="red", stroke_width="1")

        # Convert the ElementTree object to a string and return it
        return ET.tostring(svg_root, encoding="unicode", method="xml")

