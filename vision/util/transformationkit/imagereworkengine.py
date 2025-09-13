
import numpy as np
import cv2 as cv
import threading
from threading import Thread
from fastapi.responses import Response

class cameraImageWorker(Thread):
    def __init__(self):
        super().__init__()  # Call the parent class's constructor
        self.should_stop = threading.Event()
        self.cap = None

    def run(self):
        self.cap = cv.VideoCapture(0)
        if not self.cap.isOpened():
            print("Cannot open camera")
            exit()
        while not self.should_stop.is_set():
            # Capture frame-by-frame
            ret, frame = self.cap.read()

            # if frame is read correctly ret is True
            if not ret:
                print("Can't receive frame (stream end?). Exiting ...")
                break

    # When everything done, release the capture
        self.cap.release()
        cv.destroyAllWindows()

    def stop(self):
        self.should_stop.set()

camera_engine_thread = None

def init_camera_thread():
    global camera_engine_thread
    camera_engine_thread = cameraImageWorker()
    camera_engine_thread.run()
    print("starty")


def kill_camera_thread():
    global camera_engine_thread
    if camera_engine_thread:
        camera_engine_thread.stop()
        print("Camera thread stopped.")

def grab_camera_thread_capture():
    global camera_engine_thread
    if camera_engine_thread:
        ret, frame = camera_engine_thread.cap.read()
        if ret:
            _, buffer = cv.imencode('.jpg', frame)
            return Response(content=buffer.tobytes(), media_type="image/png")
    return None