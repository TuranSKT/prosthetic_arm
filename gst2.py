# Libraries
import argparse, random, os, os.path, threading, time, io, pdb
import gi
import numpy as np
from gi.repository import GLib, GObject, Gst, GstBase, Gtk
import mediapipe as mp
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands
import cv2
gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
gi.require_version('Gtk', '3.0')

#CAPS (video properties) definition
vid_width, vid_height = 640, 480

#Gstreamer Elements
SRC_CAM= "v4l2src device=/dev/video0 ! videoscale"
CAPS_VID =f"videoconvert ! video/x-raw,width={vid_width},height={vid_height},framerate=30/1"
ENC = "x264enc tune=zerolatency bitrate=1000 speed-preset=superfast ! h264parse ! rtph264pay"
UDP_SINK = "udpsink host=192.168.0.31 port=5000"
RGB_CONV = "videoconvert ! video/x-raw,format=RGB ! videoconvert"
MAIN_SINK = "appsink name=main-sink emit-signals=true max-buffers=1 drop=true"
gst_pipeline = f"""{SRC_CAM} ! {CAPS_VID} ! tee name=t ! queue ! {ENC} ! {UDP_SINK}
    t. ! queue ! {RGB_CONV} ! {MAIN_SINK}
    """
Gst.init(None)

class GstPipeline:
    def __init__(self, pipeline):
        #Gstreamer related variables
        self.running = False
        self.gstsample = None
        self.condition = threading.Condition()
        self.player = Gst.parse_launch(pipeline)

        #Fetch different pads from pipeline for manipulation
        appsink = self.player.get_by_name("main-sink")
        appsink.connect("new-preroll", self.on_new_sample, True)
        appsink.connect("new_sample", self.on_new_sample, False)

        #Src pad in which to put the model output
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)
        self.run()

    def on_new_sample(self, sink, preroll):
        sample = sink.emit('pull-preroll' if preroll else "pull-sample")
        s = sample.get_caps().get_structure(0)
        with self.condition:
            self.gstsample = sample
            self.condition.notify_all()
        return Gst.FlowReturn.OK

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.player.set_state(Gst.State.NULL)
        elif t == Gst.MessageType.ERROR:
            self.player.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print(f"error: {err}, debug: {debug}")

    def run(self):
        self.running = True
        worker = threading.Thread(target=self.main_loop)
        worker.start()
        self.player.set_state(Gst.State.PLAYING)
        try:
            Gtk.main()
        except Exception as e:
            print(e)
            pass

    def flip_array(self, target_array):
        # Flip horizontally a given array
        return np.array([row[::-1] for row in target_array])

    def main_loop(self):
        #Do inferencing or motion detection/recording given the flag
        while True:
            with self.condition:
                while not self.gstsample and self.running:
                    self.condition.wait()
                if not self.running:
                    break
                gstsample = self.gstsample
                self.gstsample = None
            gstbuffer = gstsample.get_buffer() #checked
            success, map_info = gstbuffer.map(Gst.MapFlags.READ) #checked
            if not success:
                raise RuntimeError("Could not map buffer data!")
            else:
                #get one frame
                image = np.ndarray(
                        shape=(vid_height,vid_width,3),
                        dtype=np.uint8,
                        buffer=map_info.data) #checked
                with mp_hands.Hands(
                    static_image_mode=True,
                    max_num_hands=2,
                    min_detection_confidence=0.7) as hands:
                        results = hands.process(self.flip_array(image)) #flip horizontally the image
                        if not results.multi_hand_landmarks:
                            continue
                        print(results.multi_handedness)
                        anotated_image = self.flip_array(image.copy())
                        # Draw the hand annotations on the image.
                        for hand_landmarks in results.multi_hand_landmarks:
                            mp_drawing.draw_landmarks(
                            anotated_image,
                            hand_landmarks,
                            mp_hands.HAND_CONNECTIONS,
                            mp_drawing_styles.get_default_hand_landmarks_style(),
                            mp_drawing_styles.get_default_hand_connections_style())
                gstbuffer.unmap(map_info)

def main():
    Gst.init(None)
    GstPipeline(gst_pipeline)
    GObject.threads_init()

if __name__ == "__main__":
    main()
