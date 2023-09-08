import logging
import time

import config

import cv2

import numpy as np

from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout
from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap


# Logger Setup
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d %(processName)s %(relativeCreated)d %(message)s",
    datefmt='%H:%M:%S')


def convert_to_qtimage(frame):
    h, w, ch = frame.shape
    if w != config.frame_width:
        frame = cv2.resize(frame, (config.frame_width, config.frame_height), interpolation=cv2.INTER_AREA)
        h, w, ch = frame.shape
    bytesPerLine = ch * w
    print(frame.shape)
    qtframe = QImage(frame.data, w, h, bytesPerLine, QImage.Format_BGR888)

    return qtframe


def set_cam_props(cam, cam_address):

    #cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('m', 'j', 'p', 'g'))
    #cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))

    #cam.set(cv2.CAP_PROP_FPS, config.cam_fps)

    cam.set(cv2.CAP_PROP_FRAME_WIDTH, config.frame_width)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, config.frame_height)

    cam.set(cv2.CAP_PROP_BUFFERSIZE, 3)

    #cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3) # auto mode
    #cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0) # manual mode
    #cam.set(cv2.CAP_PROP_EXPOSURE, config.cam_exposure)

    #cam.set(cv2.CAP_PROP_AUTOFOCUS, 1) # auto mode
    #cam.set(cv2.CAP_PROP_AUTOFOCUS, 0) # manual mode
    #cam.set(cv2.CAP_PROP_FOCUS, config.cam_focus)
    #cam.set(cv2.CAP_PROP_GAIN, config.cam_gain)

    pass


class CameraGrabber(QThread):
    send_image = pyqtSignal(QImage)
    camera_address = ""
    cap: cv2.VideoCapture = None

    def connect(self):
        if self.camera_address is None or self.camera_address == "":
            logger.error(f"Invalid camera address '{self.camera_address}'!")
            return False

        logger.debug(f"Connecting to camera '{self.camera_address}'..")
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()

        codec = cv2.CAP_DSHOW
        if isinstance(self.camera_address, str):
            codec = cv2.CAP_FFMPEG

        self.cap = cv2.VideoCapture(self.camera_address, codec )

        if not self.cap.isOpened():
            logger.error(f"Camera URL '{self.camera_address}' could not be opened!")
            return False

        set_cam_props(self.cap, self.camera_address)

        ret, frame = self.cap.read()
        if not ret:
            logger.error(f"Kein initiales Bild von Kamera '{self.camera_address}' erhalten! ")
            self.cap.release()
            return False
        logger.info(f"Initialer Frame von Kamera '{self.camera_address}': {frame.shape}")
        return True


    def run(self):
        logger.debug(f"Starting Grabber for camera '{self.camera_address}'")
        while True:

            if (self.cap is None) or (not self.cap.isOpened()):
                if not self.connect():
                    time.sleep(1)
                    continue

            t = time.time()
            ret, frame = self.cap.read()
            #logger.info(f"Time Elapsed: {(time.time() - t) * 1000}ms")
            if not ret:
                logger.error(f"Kein Bild von Kamera '{self.camera_address}' erhalten! ")
                self.cap.release()
                continue

            #logger.debug(type(frame))
            self.send_image.emit(convert_to_qtimage(frame))


class CameraWidget(QWidget):
    def __init__(self):
        super().__init__()
        logger.debug("__init__ called")
        self.title = 'TeEye Demo'
        self.left = 0
        self.top = 0
        self.width = 1921
        self.height = 1081
        self.init_ui()

    @pyqtSlot(QImage)
    def set_image0(self, image):
        #logger.debug("setImage() triggered")
        self.label0.setPixmap(QPixmap.fromImage(image))

    @pyqtSlot(QImage)
    def set_image1(self, image):
        # logger.debug("setImage() triggered")
        self.label1.setPixmap(QPixmap.fromImage(image))

    @pyqtSlot(QImage)
    def set_image2(self, image):
        # logger.debug("setImage() triggered")
        self.label2.setPixmap(QPixmap.fromImage(image))

    @pyqtSlot(QImage)
    def set_image3(self, image):
        # logger.debug("setImage() triggered")
        self.label3.setPixmap(QPixmap.fromImage(image))

    def init_ui(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        ml = QGridLayout()
        self.setLayout(ml)



        #self.resize(1920, 1080)

        # create a label
        self.label0 = QLabel(self)
        #self.label.move(280, 120)
        self.label0.resize(640, 480)

        self.label1 = QLabel(self)
        # self.label.move(280, 120)
        self.label1.resize(640, 480)

        self.label2 = QLabel(self)
        # self.label.move(280, 120)
        self.label2.resize(640, 480)

        self.label3 = QLabel(self)
        # self.label.move(280, 120)
        self.label2.resize(640, 480)

        ml.addWidget(self.label0, 0, 0, 1, 1)
        ml.addWidget(self.label1, 0, 1, 1, 1)
        ml.addWidget(self.label2, 1, 0, 1, 1)
        ml.addWidget(self.label3, 1, 1, 1, 1)

        th0 = CameraGrabber()
        th0.camera_address = 0
        th0.send_image.connect(self.set_image0)
        th0.start()

        #th1 = CameraGrabber(self)
        #th1.camera_address = 1
        #th1.send_image.connect(self.set_image1)
        #th1.start()

        #th2 = CameraGrabber(self)
        #th2.camera_address =  'rtsp://admin:111111@172.16.2.6:554/h264Preview_01_main'
        #th2.send_image.connect(self.set_image2)
        #th2.start()

        self.show()