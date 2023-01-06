"""Common utilities."""
import xml.etree.ElementTree as ET
import numpy as np

def flip_array(target_array):
  # Flip horizontally a given array
  return np.array([row[::-1] for row in target_array])

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

