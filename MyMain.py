import logging
import multiprocessing as mp
import os
import signal
import sys
import threading
import time

import cv2

from PyQt5.QtWidgets import  QWidget, QLabel, QApplication

import AppWidget


# Logger Setup
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d %(processName)s %(relativeCreated)d %(message)s",
    datefmt='%H:%M:%S')

stop_event = mp.Event()

# Signalhandling
def handler(signalname):
    """
    Python 3.9 has `signal.strsignal(signalnum)` so this closure would not be needed.
    Also, 3.8 includes `signal.valid_signals()` that can be used to create a mapping for the same purpose.
    """

    def f(signal_received, frame):
        logger.info(f"SingalHandler: {signalname} received!")
        stop_event.set()

    return f


def cam_launch(stop_event: mp.Event()):
    cap_0 = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    ret0, frame0 = cap_0.read()
    cv2.imshow(f"Initial image", frame0)
    cv2.waitKey(0)

    while not stop_event.is_set():
        #Check for unregistered cameras
        for i in range(4):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap is None or not cap.isOpened():
                print(f"Unable to open cam {i}")
                continue

            ret, frame = cap.read()
            cv2.imshow(f"Frame of Cam {i}", frame)
            cv2.waitKey(1000)
            #Connect
            #TODO
            cv2.destroyWindow(f"Frame of Cam {i}")

        time.sleep(0.5)

    logger.info("CamLauncher exiting.")


if __name__ == '__main__':
    logger.info("Starting..")
    logger.info(f"..Python Version: {sys.version.split(' ')[0]}")
    logger.info(f"..OpenCV Version: {cv2.__version__}")

    os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;udp'

    # Signal-Handler für Shutdown-Signale einsetzen
    signal.signal(signal.SIGINT, handler("SIGINT"))
    signal.signal(signal.SIGTERM, handler("SIGTERM"))

    # Setup von Events und Queues


    # Starte alle Prozesse
    cam_laucher_p: mp.Process = mp.Process(
        name="CamLauncher", daemon=True, target=cam_launch,
        args=(stop_event,))
        #(detection_to_logic_pipe_output, logic_to_gui_pipe_input, sim_to_led_pipe_input,
              #sim_to_belt_controller_pipe_input, stop_event))
    cam_laucher_p.start()


    # Starte die GUI
    # Some setup for qt
    logger.debug("Starting GUI..")
    app = QApplication(sys.argv)
    window = AppWidget.CameraWidget()
    app.exec_()

    # Hintergrundprozesse beenden
    logger.debug("GUI stopped. Stopping background processes.")
    stop_event.set()
    # Warte auf Beendigung aller Prozesse
    logger.info("Waiting for all processes to terminate..")
    processes = [cam_laucher_p]
    while any([p.is_alive() for p in processes]):
        time.sleep(0.1)

    time.sleep(0.2)
    logger.info("Main Thread exited!")