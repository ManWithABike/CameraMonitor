from PyQt5 import QtCore, QtWidgets
import qdarkstyle
from threading import Thread
from collections import deque
from datetime import datetime
import time
import sys
import cv2
import imutils


class CameraWidget(QtWidgets.QWidget):
    """Independent camera feed
    Uses threading to grab IP camera frames in the background

    @param width - Width of the video frame
    @param height - Height of the video frame
    @param stream_link - IP/RTSP/Webcam link
    @param aspect_ratio - Whether to maintain frame aspect ratio or force into fraame
    """

    def __init__(self, width, height, stream_link=0, aspect_ratio=False, parent=None, deque_size=1):
        super(CameraWidget, self).__init__(parent)

        # Initialize deque used to store frames read from the stream
        self.deque = deque(maxlen=deque_size)

        # Slight offset is needed since PyQt layouts have a built in padding
        # So add offset to counter the padding
        self.offset = 16
        self.screen_width = width - self.offset
        self.screen_height = height - self.offset
        self.maintain_aspect_ratio = aspect_ratio

        self.camera_stream_link = stream_link

        # Flag to check if camera is valid/working
        self.online = False
        self.capture = None
        self.video_frame = QtWidgets.QLabel()

        self.load_network_stream()

        # Start background frame grabbing
        self.get_frame_thread = Thread(target=self.get_frame, args=())
        self.get_frame_thread.daemon = True
        self.get_frame_thread.start()

        # Periodically set video frame to display
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.set_frame)
        self.timer.start(500)

        print('Started camera: {}'.format(self.camera_stream_link))

    def load_network_stream(self):
        """Verifies stream link and open new stream if valid"""

        def load_network_stream_thread():
            if self.verify_network_stream(self.camera_stream_link):
                self.capture = cv2.VideoCapture(self.camera_stream_link)
                self.online = True
            else:
                print("Stream not verified!")

        self.load_stream_thread = Thread(target=load_network_stream_thread, args=())
        self.load_stream_thread.daemon = True
        self.load_stream_thread.start()

    def verify_network_stream(self, link):
        """Attempts to receive a frame from given link"""

        cap = cv2.VideoCapture(link)
        if not cap.isOpened():
            print("Stream not opened: " + link + " (type:" + type(link) + ")")
            return False
        cap.release()
        return True

    def get_frame(self):
        """Reads frame, resizes, and converts image to pixmap"""

        while True:
            try:
                if self.capture.isOpened() and self.online:
                    # Read next frame from stream and insert into deque
                    status, frame = self.capture.read()
                    print (frame.shape)
                    cv2.imshow("Test", frame)
                    cv2.waitKey(1)
                    if status:
                        self.deque.append(frame)
                    else:
                        self.capture.release()
                        self.online = False
                else:
                    # Attempt to reconnect
                    print('attempting to reconnect', self.camera_stream_link)
                    self.load_network_stream()
                    self.spin(2)
                self.spin(.001)
            except AttributeError:
                pass

    def spin(self, seconds):
        """Pause for set amount of seconds, replaces time.sleep so program doesnt stall"""

        time_end = time.time() + seconds
        while time.time() < time_end:
            QtWidgets.QApplication.processEvents()

    def set_frame(self):
        """Sets pixmap image to video frame"""
        print("setting frame")
        if not self.online:
            print("Not Online")
            self.spin(1)
            return

        if self.deque and self.online:
            # Grab latest frame
            frame = self.deque[-1]
            print(frame.shape)
            # Keep frame aspect ratio
            if self.maintain_aspect_ratio:
                self.frame = imutils.resize(frame, width=self.screen_width)
            # Force resize
            else:
                self.frame = cv2.resize(frame, (self.screen_width, self.screen_height))

            # Add timestamp to cameras
            cv2.rectangle(self.frame, (self.screen_width - 190, 0), (self.screen_width, 50), color=(0, 0, 0),
                          thickness=-1)
            cv2.putText(self.frame, datetime.now().strftime('%H:%M:%S'), (self.screen_width - 185, 37),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), lineType=cv2.LINE_AA)

            # Convert to pixmap and set to video frame
            self.img = QtWidgets.QImage(self.frame, self.frame.shape[1], self.frame.shape[0],
                                    QtWidgets.QImage.Format_RGB888).rgbSwapped()
            self.pix = QtWidgets.QPixmap.fromImage(self.img)
            self.video_frame.setPixmap(self.pix)

    def get_video_frame(self):
        print("returning Frame")
        return self.video_frame


def exit_application():
    """Exit program event handler"""

    sys.exit(1)


if __name__ == '__main__':

    # Create main application window
    app = QtWidgets.QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setStyle(QtWidgets.QStyleFactory.create("Cleanlooks"))
    mw = QtWidgets.QMainWindow()
    mw.setWindowTitle('Camera GUI')
    mw.setWindowFlags(QtCore.Qt.FramelessWindowHint)

    cw = QtWidgets.QWidget()
    ml = QtWidgets.QGridLayout()
    cw.setLayout(ml)
    mw.setCentralWidget(cw)
    mw.showMaximized()

    # Dynamically determine screen width/height
    screen_width = QtWidgets.QApplication.desktop().screenGeometry().width()
    screen_height = QtWidgets.QApplication.desktop().screenGeometry().height()

    # Create Camera Widgets 
    username = 'Your camera username!'
    password = 'Your camera password!'

    # Stream links
    camera0 = 1
    #camera1 = '1'
    #cameraX = 'rtsp://{}:{}@192.168.1.43:554/cam/realmonitor?channel=1&subtype=0'.format(username, password)
    #cameraY = 'rtsp://admin:111111@172.16.2.5:554/h264Preview_01_main'


    # Create camera widgets
    print('Creating Camera Widgets...')
    zero = CameraWidget(screen_width // 3, screen_height // 3, camera0)
    #one = CameraWidget(screen_width // 3, screen_height // 3, camera1)

    # Add widgets to layout
    print('Adding widgets to layout...')
    ml.addWidget(zero.get_frame(), 0, 0, 1, 1)
    #ml.addWidget(one.get_video_frame(), 0, 1, 1, 1)
    #ml.addWidget(two.get_video_frame(), 0, 2, 1, 1)
    #ml.addWidget(three.get_video_frame(), 1, 0, 1, 1)
    #ml.addWidget(four.get_video_frame(), 1, 1, 1, 1)
    #ml.addWidget(five.get_video_frame(), 1, 2, 1, 1)
    #ml.addWidget(six.get_video_frame(), 2, 0, 1, 1)
    #ml.addWidget(seven.get_video_frame(), 2, 1, 1, 1)

    print('Verifying camera credentials...')

    mw.show()

    #QtWidgets.QShortcut(QtWidgets.QKeySequenceEdit('Ctrl+Q'), mw, exit_application)

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtWidgets.QApplication.instance().exec_()