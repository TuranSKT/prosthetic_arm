# Prosthetic Arm

This repository contains a personal project of mine which is a prosthetic arm that can copy the movements of a subject using a webcam and a Raspberry Pi4. </br>
The ultimate goal is to replicate the movements on a robotic arm using servo motors. </br>

## Contents

The repository contains the following files:</br>

- `streamer.py`: This script uses a Gstreamer pipeline to stream the video from a webcam (Logitech c930e) on a Raspberry Pi to a PC in a local network. It also performs hand and finger detection using the MediaPipe API from Google and draws hand landmarks directly on the streamed video, so that they can be seen on the client side. Meanwhile landmarks are analysed in real-time (with --buffer set to 1) or over multiple frames (with --buffer > 1) to compute angles that help to determine finger states. Arguments -min and -max act as threshold to calibrate the sensibility of the arm. </br>

- `utility.py`: This file contains utility functions.</br>

- `prosthetic_arm.py`: This file contains some basic GPIO-related commands to test servo motors and move the prosthetic arm plugged to the Pi4.</br>

## Usage

Example of usage :</br>

``` 
python streamer.py -min 0.1 -max 1 -buffer 1
```
Note that the Gstreamer pipeline in `streamer.py` has been inspired by the Google Coral work.</br>

## Requirements 
### Server side
Python
``` 
sudo apt-get install python3-venv python3-dev 
```
Gstreamer 
``` 
sudo apt-get install gstreamer1.0-tools gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly gstreamer1.0-plugins-bad gstreamer1.0-libav python3-gi python3-gi-cairo gir1.2-gtk-3.0 gi libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev gobject-introspection python3-gst-1.0 
```
``` 
pip install PyGObject 
```
Hand detection (Mediapipe)
``` 
pip install mediapipe 
```
GPIO 
``` 
pip install RPi.GPIO 
```
