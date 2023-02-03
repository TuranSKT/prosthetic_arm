import xml.etree.ElementTree as ET


class SVG:
    '''
    Creates a SVG element dicts that will help to draw landmarks in 
    real-time in the Gstreamer video stream
    :param landmarks_dict (dict) : dict that contains landmarks of all
    fingers in the current frame
    :param connections_dict (dict) : dict that helps to bind landmarks in 
    order to create fingers
    :param src_size (1D array) : video source resolution [width, height]
    '''
    def __init__(self, src_size):
        self.src_size = src_size
        self.landmarks_dict = None
        self.connections_dict = None

    def create_svg(self, landmarks_dict, connections_dict):
        self.landmarks_dict = landmarks_dict
        self.connections_dict = connections_dict

        #Create the root element
        svg_root = ET.Element("svg", 
                width=str(self.src_size[0]), 
                height=str(self.src_size[1]))

        # Add a circle element for each point in the dictionary
        for landmark, coords in self.landmarks_dict.items():
            ET.SubElement(svg_root, 
                    "circle", 
                    cx=str(coords[0]), 
                    cy=str(coords[1]), 
                    r="2")

        # Add a line element for each line in the dictionary
        for connection, lines in self.connections_dict.items():
            for line in lines:
                p1 = self.landmarks_dict[str(line[0])]
                p2 = self.landmarks_dict[str(line[1])]
                ET.SubElement(svg_root, 
                        "line", 
                        x1=str(p1[0]), y1=str(p1[1]), 
                        x2=str(p2[0]), y2=str(p2[1]), 
                        stroke="red", stroke_width="1")

        # Convert the ElementTree object to a string and return it
        return ET.tostring(svg_root, encoding="unicode", method="xml")

