
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

def aruco_marker_capture():
    global camera_engine_thread
    if camera_engine_thread:
        aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_6X6_250)
        parameters = cv.aruco.DetectorParameters()
        ret, frame = camera_engine_thread.cap.read()
        detector = cv.aruco.ArucoDetector(aruco_dict, parameters)
        if ret:
            marker_corners, marker_ids, _ = detector.detectMarkers(frame)
            outImage: cv.Mat = frame.copy()
            cv.aruco.drawDetectedMarkers(outImage, marker_corners, marker_ids)
            _, buffer = cv.imencode('.png', outImage)
            return Response(content=buffer.tobytes(), media_type="image/png")
    return None

def position_correction_capture():
    global cmaera_engine_thread
    if camera_engine_thread:
        aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_6X6_250)
        parameters = cv.aruco.DetectorParameters()
        detector = cv.aruco.ArucoDetector(aruco_dict, parameters)
        ret, frame = camera_engine_thread.cap.read()
        if ret:
            marker_corners, marker_ids, _ = detector.detectMarkers(frame)
            if marker_ids is not None and len(marker_ids) > 0 and [1,2,3,4] in marker_ids:
                # Get the corners of the markers
                corners_dict = {id[0]: corner for id, corner in zip(marker_ids, marker_corners)}
                # Assuming markers 1, 2, 3, and 4 are present
                pts1 = np.array([corners_dict[i][0][0] for i in [1, 2, 3, 4]], dtype="float32")
                # Define the destination points for a top-down view
                size = 500
                pts2 = np.array([[0, 0], [size - 1, 0], [size - 1, size - 1], [0, size - 1]], dtype="float32")
                # Compute the perspective transform matrix
                M = cv.getPerspectiveTransform(pts1, pts2)
                # Apply the perspective transformation to get the corrected image
                warped = cv.warpPerspective(frame, M, (size, size))
                _, buffer = cv.imencode('.png', warped)
                return Response(content=buffer.tobytes(), media_type="image/png")
    return None
            