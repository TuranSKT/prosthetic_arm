# Prosthetic Arm

This repository contains a personal project of mine which is a prosthetic arm that can copy the movements of a subject using a webcam and a Raspberry Pi4. </br>
The ultimate goal is to replicate the movements on a robotic arm using servo motors. </br>

## Contents

The repository contains the following files:</br>

- `streamer.py`: This script uses a Gstreamer pipeline to stream the video from a webcam (Logitech c930e) on a Raspberry Pi to a PC in a local network. It also performs hand and finger detection using the MediaPipe of Google and draws hand landmarks directly on the streamed video, so that they can be seen on the client side.</br>

- `utility.py`: This file contains some utility functions, including the `SVG` class that allows to draw SVG landmarks.</br>

- `prosthetic_arm.py`: This file contains some basic GPIO-related commands to control servo motors and move a robotic arm plugged to the Raspberry Pi.</br>

## Usage

To run the code, use the following command:</br>

``` 
python streamer.py 
```
Note that the Gstreamer pipeline in `streamer.py` has been inspired by the Google Coral works.</br>

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
