# Prosthetic Arm
This repository contains a personal project of mine which is a prosthetic arm that can copy the movements of a subject using a webcam and a Raspberry Pi4. The ultimate goal is to replicate the movements on a robotic arm using servo motors. </br>
**[On-going feature] Ability to use electrodes as inputs instead of a webcam.**
<img src="/images/header.png" width="50%" height="50%">
## Contents

The following files are included in this repository:</br>

- `streamer.py`: This script uses a Gstreamer pipeline (inspired by the Google Coral example) to captures video from a device (Logitech c930e webcam) and then divide the video stream into two trees. The first one overlays the video with an SVG image and then sends from a Raspberry Pi to a network local address. The second one is filters the video and then renders it to a video sink, where the main inference loop happens and the overlay object is created. The main loop performs hand and finger detection using Google's MediaPipe and draws hand landmarks directly on the streamed video, allowing for real-time visualization on the client side. 
Meanwhile landmarks are analysed in real-time to compute angles that help to determine finger states (extension, and flexion). </br>

- `utility.py`: This file contains utility functions.</br>

- `svg_landmarks`: SVG class. Creates a SVG object in which landmarks coordinates of the fingers are represented as circles (finger joints) and landmarks connections as lines (bones).</br>

- `gpio_servos`: Everything related to the control of the servos.</br>

## Usage
Example of usage :</br>
``` 
# (Server side)
python streamer.py -angle 0.1 -fps 30
```
-angle: Angle threshold from which a fingers state is considered as flexion.</br>
-fps: Set video input/output FPS "</br>

```
# (Client side) To visualise the inference output
gst-launch-1.0 -v udpsrc port=5000 ! application/x-rtp, payload=96 ! rtph264depay ! decodebin ! videoconvert ! autovideosink
```
## Requirements 
System requirements
``` 
sudo apt-get install python3-venv python3-dev 
```
``` 
sudo apt-get install gstreamer1.0-tools gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly gstreamer1.0-plugins-bad gstreamer1.0-libav python3-gi python3-gi-cairo gir1.2-gtk-3.0 gi libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev gobject-introspection python3-gst-1.0 
```
Python requirements
``` 
pip install requirements
```

## Hardware 
Raspberry Pi 4 (8GB)</br>
Logitech c930e webcam</br>
Prosthetic arm with 5 SG90 servos</br>
2x 470μF capacitors

## External links 
Mediapipe API</br>
https://google.github.io/mediapipe/solutions/hands.html</br>
Google example use of Gstreamer pipeline (Coral)</br>
https://github.com/google-coral/examples-camera/blob/master/gstreamer/gstreamer.py</br>
Prosthetic arm 3D model</br>
https://www.thingiverse.com/thing:4807141</br>

