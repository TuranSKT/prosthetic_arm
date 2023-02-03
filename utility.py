import math

def process_landmarks(landmarks, image_height, image_width):
    """
    Converts a list of landmarks into a list of lists of coordinates.
    :param landmarks (List[landmark]): A list of landmarks to be converted.
    :param image_height (int): Height of the image.
    :param image_width (int): Width of the image.
    :return: A list of lists containing the x, y, z coordinates of each landmark
    in the given image.
    """
    processed_landmarks = []
    for landmark in landmarks[0].landmark:
        processed_landmarks.append([landmark.x*image_width, 
                            landmark.y*image_height, 
                            landmark.z])
    return processed_landmarks


def get_angle(finger_landmarks):
    '''
    Given the landmarks of one single finger, 
    creates 2 vectors to compute a "bend" angle to 
    determine whether the state of a finger ("extension" or "flexion").
    :param finger_landmarks (list) : Landmarks of one single finger
    :return angle (float) : Angle between 2 defined vectors that represents 
    finger's joints
    '''
    # Define vectors between the first and second landmarks and the last and 
    #second landmarks
    v1 = [finger_landmarks[1][0]-finger_landmarks[0][0], 
            finger_landmarks[1][1]-finger_landmarks[0][1], 
            finger_landmarks[1][2]-finger_landmarks[0][2]]
    v2 = [finger_landmarks[2][0]-finger_landmarks[1][0], 
            finger_landmarks[2][1]-finger_landmarks[1][1], 
            finger_landmarks[2][2]-finger_landmarks[1][2]]
    
    # Calculate the dot product and magnitude of the vectors
    dot = v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]
    mag1 = math.sqrt(v1[0]**2 + v1[1]**2 + v1[2]**2)
    mag2 = math.sqrt(v2[0]**2 + v2[1]**2 + v2[2]**2)

    # Calculate the angle between the vectors
    angle = math.acos(dot/(mag1*mag2))
    return angle


def thresholder(angle, threshold):
    '''
    Given a threshold, determines whether a state is "flexion" or "extension"
    :param angle (float) : Angle between 2 defined vectors that represents 
    finger's joints
    :param threshold (float)
    :return string : Returns the state of the finger
    '''
    if angle > threshold:
        return "flexion"
    else:
        return "extension"

def state_detector(landmarks, threshold):
    '''
    Loops through each finger in landmakrs and determine the state of a finger
    i.e "flexion" or "extension".
    :param landmarks (list) : list of landmarks of all fingers detected in the
    current frame
    :param threshold (float) : angle threshold from which the fingers' state
    is considered as "flexion" or "extension"
    :return states (dict) : dictionnary of states of all fingers in the current 
    frame
    '''
    fingers = ["thumb", "index", "middle", "ring", "pinky"]
    states = {}

    # Iterate through each finger
    for i in range(1, 21, 4):

        # Get the landmarks for the current finger
        finger_landmarks = landmarks[i:i+4]
        angle = get_angle(finger_landmarks)

        # Determine the state of the finger based on the angles
        if i//4: #all fingers except the thumb
            states[fingers[i//4]] = thresholder(angle, threshold)
        else: # thumb only
            states[fingers[i//4]] = thresholder(angle, 0.1)
    return states


def get_hand_connections_dict():
    '''
    Returns a dict that helps to bind landmarks to "create" fingers
    '''
    hand_connections_dict = {
        "hand_palm_connections": [(0, 1), (0, 5), (9, 13), 
                                 (13, 17), (5, 9), (0, 17)],
        "hand_thumb_connections": [(1, 2), (2, 3), (3, 4)],
        "hand_index_finger_connections": [(5, 6), (6, 7), (7, 8)],
        "hand_middle_finger_connections": [(9, 10), (10, 11), (11, 12)],
        "hand_ring_finger_connections": [(13, 14), (14, 15), (15, 16)],
        "hand_pinky_finger_connections": [(17, 18), (18, 19), (19, 20)],
    }
    return hand_connections_dict
