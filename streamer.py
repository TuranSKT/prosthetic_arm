import sys
import threading
import argparse
import numpy as np
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, GObject, Gst, GstBase, Gtk

from utility import SVG, flip_array, state_detector, process_landmarks, PROSTHETIC_HAND_GPIO

import mediapipe as mp
mp_hands = mp.solutions.hands

Gst.init(None)
class LandmarkBuffer:
    def __init__(self):
        self.landmarks_mean = []

    def get_landmarks_mean(self):
        return self.landmarks_mean

    def reset(self):
        self.landmarks_mean = []

    def update_landmarks_mean(self, new_landmarks):
        if len(self.landmarks_mean) == 0:
            self.landmarks_mean = new_landmarks
        else: 
            #self.landmarks_mean = [(x1+x2)/2 for (x1,x2) in zip(self.landmarks_mean, new_landmarks)]
            self.landmarks_mean = [[(x1+x2)/2, (y1+y2)/2, (z1+z2)/2] for (x1,y1,z1), (x2,y2,z2) in zip(self.landmarks_mean, new_landmarks)]


class GstPipeline:
    def __init__(self, pipeline, src_size, ext, flex, buff):
        self.running = False
        self.gstsample = None
        self.sink_size = None
        self.condition = threading.Condition()
        self.source_size = src_size
        self.pipeline = Gst.parse_launch(pipeline)
        self.overlay = self.pipeline.get_by_name('overlay')
        self.extension_thresh = ext
        self.flexion_thresh = flex
        self.buffer_max_size = buff
        self.landmark_buffer_nb = 0
        appsink = self.pipeline.get_by_name('appsink')
        appsink.connect('new-preroll', self.on_new_sample, True)
        appsink.connect('new-sample', self.on_new_sample, False)

        # Set up a pipeline bus watch to catch errors.
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_bus_message)

    def run(self):
        # Start inference worker.
        self.running = True
        worker = threading.Thread(target=self.inference_loop)
        worker.start()

        # Run pipeline.
        self.pipeline.set_state(Gst.State.PLAYING)
        try:
            Gtk.main()
        except:
            pass

        # Clean up.
        self.pipeline.set_state(Gst.State.NULL)
        while GLib.MainContext.default().iteration(False):
            pass
        with self.condition:
            self.running = False
            self.condition.notify_all()
        worker.join()

    def on_bus_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            Gtk.main_quit()
        elif t == Gst.MessageType.WARNING:
            err, debug = message.parse_warning()
            sys.stderr.write('Warning: %s: %s\n' % (err, debug))
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            sys.stderr.write('Error: %s: %s\n' % (err, debug))
            Gtk.main_quit()
        return True

    def on_new_sample(self, sink, preroll):
        sample = sink.emit('pull-preroll' if preroll else 'pull-sample')
        if not self.sink_size:
            s = sample.get_caps().get_structure(0)
            self.sink_size = (s.get_value('width'), s.get_value('height'))
        with self.condition:
            self.gstsample = sample
            self.condition.notify_all()
        return Gst.FlowReturn.OK

    def buffer2array(self, gst_buffer):
        success, map_info = gst_buffer.map(Gst.MapFlags.READ) #checked
        if not success:
            raise RuntimeError("Could not map buffer data!")
        else:
            array = np.ndarray(
                    shape=(self.source_size[1],self.source_size[0],3),
                    dtype=np.uint8,
                    buffer=map_info.data)
        return array, map_info

    def get_hand_landmarks_position(self, hand_landmarks):
        image_width, image_height = self.source_size[0], self.source_size[1]
        hand_landmarks_dict = {}
        for i, landmark_type in enumerate(mp_hands.HandLandmark):
            hand_landmarks_dict[str(i)] = [
                hand_landmarks.landmark[landmark_type].x * image_width,
                hand_landmarks.landmark[landmark_type].y * image_height
            ]
        return hand_landmarks_dict

    def get_hand_connections_dict(self):
        hand_connections_dict = {
            "hand_palm_connections": [(0, 1), (0, 5), (9, 13), (13, 17), (5, 9), (0, 17)],
            "hand_thumb_connections": [(1, 2), (2, 3), (3, 4)],
            "hand_index_finger_connections": [(5, 6), (6, 7), (7, 8)],
            "hand_middle_finger_connections": [(9, 10), (10, 11), (11, 12)],
            "hand_ring_finger_connections": [(13, 14), (14, 15), (15, 16)],
            "hand_pinky_finger_connections": [(17, 18), (18, 19), (19, 20)],
        }
        return hand_connections_dict

    def generate_svg(self, dict_points, dict_lines):
        return SVG(dict_points, dict_lines, self.source_size).create_svg()

    def inference_loop(self):
        loop_bool = True
        gpio_thread = PROSTHETIC_HAND_GPIO()
        landmark_buffer = LandmarkBuffer()
        while loop_bool:
            with self.condition:
                while not self.gstsample and self.running:
                    self.condition.wait()
                if not self.running:
                    break
                gstsample = self.gstsample
                self.gstsample = None

            # Passing Gst.Buffer as input tensor avoids 2 copies of it.
            gstbuffer = gstsample.get_buffer()

            # Convert buffer to numpy frame
            np_frame, map_info = self.buffer2array(gstbuffer)

            with mp_hands.Hands(
                static_image_mode=True,
                max_num_hands=1,
                min_detection_confidence=0.7) as hands:
                    results = hands.process(np_frame)
                    landmarks = results.multi_hand_landmarks
                    if not landmarks :
                        continue
                    #print(landmarks)
                    landmark_buffer.update_landmarks_mean(process_landmarks(landmarks,
                            self.source_size[1],
                            self.source_size[0]))
                    if self.landmark_buffer_nb == self.buffer_max_size:
                        states = state_detector(landmark_buffer.get_landmarks_mean(), 
                            self.extension_thresh, 
                            self.flexion_thresh)
                        gpio_thread.move_motors(states)
                        landmark_buffer.reset()
                        self.landmark_buffer_nb = 0
                        print(states)
                    for hand_landmarks in landmarks:
                        dict_points = self.get_hand_landmarks_position(hand_landmarks)
                        dict_lines = self.get_hand_connections_dict()
                        svg = self.generate_svg(dict_points, dict_lines)
                        self.overlay.set_property('data', svg)
            bus = self.pipeline.get_bus()
            gstbuffer.unmap(map_info)
            self.landmark_buffer_nb += 1

def run_pipeline(ext, flex, buff):
    ip_addr = '192.168.0.31'
    vid_width, vid_height = 176,144
    src_size=(vid_width, vid_height)

    #Main tee
    videosrc = '/dev/video0'
    #h264_enc = "qtdemux ! queue ! h264parse ! avdec_h264 ! videoconvert"
    src_caps = f'video/x-raw,width={vid_width},height={vid_height},framerate=30/1'

    #Streaming tee
    #stream_enc = "jpegenc ! rtpjpegpay"
    stream_enc = 'x264enc tune=zerolatency bitrate=1000 speed-preset=superfast'
    stream_udp = f'udpsink host={ip_addr} port=5000'

    #Inference tee
    sink_caps = f'video/x-raw,format=RGB'
    sink_element = 'appsink name=appsink emit-signals=true max-buffers=1 drop=true'

    #Leak for both tees
    leaky_q = 'queue max-size-buffers=1 leaky=downstream'

    pipeline = f'''v4l2src device={videosrc} ! {src_caps} ! videoconvert ! tee name=t
        t. ! {leaky_q} ! rsvgoverlay name =overlay ! videoconvert ! {stream_enc} ! h264parse ! rtph264pay ! {stream_udp}
        t. ! {leaky_q} ! videoconvert ! {sink_caps} ! {sink_element}
        '''

    #print('Gstreamer pipeline:\n', pipeline)
    pipeline = GstPipeline(pipeline, src_size, ext, flex, buff)
    pipeline.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Detect objects from webcam images')
    parser.add_argument('-min', '--extension_threshold', type=float, default=0, help='Mininmum angle threshold')
    parser.add_argument('-max', '--flexion_threshold', type=float, default=0, help='Maximum angle threshold')
    parser.add_argument('-buffer', '--max_nb_buffer', type=int, default=0, help='Number of loop to wait before computing landmarks means')
    args = parser.parse_args()
    run_pipeline(args.extension_threshold, args.flexion_threshold, args.max_nb_buffer)
