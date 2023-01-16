# Prosthetic Arm
This repository contains a personal project of mine which is a prosthetic arm that can copy the movements of a subject using a webcam and a Raspberry Pi4. The ultimate goal is to replicate the movements on a robotic arm using servo motors. </br>
**[On-going feature] Ability to use electrodes as inputs instead of a webcam.**
<img src="/images/header.png" width="50%" height="50%">
## Contents

The following files are included in this repository:</br>

- `streamer.py`: This script uses a Gstreamer pipeline (inspired by the Google Coral example) to captures video from a device (Logitech c930e webcam) and then divide the video stream into two trees. The first one overlays the video with an SVG image and then sends from a Raspberry Pi to a network local address. The second one is filters the video and then renders it to a video sink, where the main inference loop happens and the overlay object is created. The main loop performs hand and finger detection using Google's MediaPipe and draws hand landmarks directly on the streamed video, allowing for real-time visualization on the client side. 
Meanwhile landmarks are analysed in real-time to compute angles that help to determine finger states (extension, flexion and middle). </br>

- `utility.py`: This file contains utility functions.</br>

- `prosthetic_arm.py`: This file contains basic commands for controlling servo motors and moving a robotic arm connected to the Raspberry Pi using GPIO. It is completely independant from the other previous files.</br>

## Usage
Example of usage :</br>
``` 
# (Server side)
python streamer.py -min 0.1 -max 1 -buffer 1
```
-buffer: number of frames to wait before computing fingers state analyses. The mean coordinnate of each landmarks is calculated over "-buffer" number of frames.</br>
-min: min angle from which the state of the finger is considered as "extension"</br>
-max: max angle from which the state of the finger is considered as "flexion". </br>
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

Asus ROG Zephyrus G14 GA401IV</br>
CPU : AMD Ryzen 9 4900HS </br>
iGPU : AMD ATI 04:00.0 Renoir</br>
GPU : NVIDIA GeForce RTX 2060 M</br>
OS : Pop_OS 22.04</br>

## External links 
Mediapipe API</br>
https://google.github.io/mediapipe/solutions/hands.html</br>
Google example use of Gstreamer pipeline (Coral)</br>
https://github.com/google-coral/examples-camera/blob/master/gstreamer/gstreamer.py</br>
Prosthetic arm 3D model</br>
https://www.thingiverse.com/thing:4807141</br>

