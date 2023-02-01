# Common utilites libraries
import sys
import threading
import argparse
import numpy as np

# Gstreamer related
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, GObject, Gst, GstBase, Gtk

# Mediapipe
import mediapipe as mp
mp_hands = mp.solutions.hands

# Custom libraries
from utility import state_detector, process_landmarks, get_hand_connections_dict
from svg_landmarks import SVG
from gpio_servos import PROSTHETIC_HAND_GPIO

Gst.init(None)


class GstPipeline:
    '''
    Main Gstreamer Pipeline. Heavily inspired from Google's Coral example that 
    utilises a main inference sink.
    '''
    def __init__(self, pipeline, src_size, angle):
        self.running = False
        self.gstsample = None
        self.sink_size = None
        self.condition = threading.Condition()
        self.source_size = src_size
        self.pipeline = Gst.parse_launch(pipeline)
        self.overlay = self.pipeline.get_by_name('overlay')
        self.angle_threshold = angle
        self.gpio_thread = PROSTHETIC_HAND_GPIO()

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
            self.gpio_thread.cleaner()
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
        '''
        Convert a gst_buffer element into a readable array
        :param gst_buffer (gi.repository.Gst.Buffer) : Gst buffer of the current frame
        :return array, map_info (np.array, gst.map) : the current frame in the 
        form of a np array. Map info is needed in the main loop to free gst
        ressources.
        '''
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
        '''
        Convert a Mediapipe landmarks object into a dict that only contains
        x,y positions of each finger's landmarks
        :param hand_landmarks (mediapipe.framework.formats.landmark_pb2.NormalizedLandmarkList)
        :return hand_landmarks_dict (dict) : dict that only contains x,y
        coordinates
        '''
        image_width, image_height = self.source_size[0], self.source_size[1]
        hand_landmarks_dict = {}
        for i, landmark_type in enumerate(mp_hands.HandLandmark):
            hand_landmarks_dict[str(i)] = [
                hand_landmarks.landmark[landmark_type].x * image_width,
                hand_landmarks.landmark[landmark_type].y * image_height
            ]
        return hand_landmarks_dict


    def inference_loop(self):
        loop_bool = True

        # Creates the SVG overlay of the hand 
        svg_overlay = SVG(self.source_size)

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

            # Mediapipe hand landmarks detection
            with mp_hands.Hands(
                static_image_mode=True,
                max_num_hands=1,
                min_detection_confidence=0.7) as hands:
                    results = hands.process(np_frame)
                    landmarks = results.multi_hand_landmarks
                    if not landmarks :
                        continue
                    processed_landmarks = process_landmarks(landmarks,
                            self.source_size[1],
                            self.source_size[0])

                    # Given the detected landmarks assign a states
                    # "extension" or "flexion" to each finger
                    states = state_detector(processed_landmarks, self.angle_threshold)

                    # Move servos of the prosthetic hand accordingly
                    self.gpio_thread.move_motors(states)
                    print(states)
                    
                    # Draw SVG of the detected landmark as overlay client side
                    # Directly in the video stream
                    for hand_landmarks in landmarks:
                        dict_points = self.get_hand_landmarks_position(hand_landmarks)
                        dict_lines = get_hand_connections_dict()
                        svg = svg_overlay.create_svg(dict_points, dict_lines)
                        self.overlay.set_property('data', svg)

            # Catch errors
            bus = self.pipeline.get_bus()

            # Free Gst ressources
            gstbuffer.unmap(map_info)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-angle_thresh', '--angle_threshold', type=float, default=0.1, 
            help='Angle threshold from which a fingers state is considered as flexion')
    args = parser.parse_args()

    ip_addr = '192.XXX.X.XX'
    vid_width, vid_height = 176,144
    src_size=(vid_width, vid_height)

    #Main tee
    videosrc = '/dev/video0'
    src_caps = f'video/x-raw,width={vid_width},height={vid_height},framerate=30/1'

    #Streaming tee
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

    print('Gstreamer pipeline:\n', pipeline)
    pipeline = GstPipeline(pipeline, src_size, args.angle_threshold)
    pipeline.run()
