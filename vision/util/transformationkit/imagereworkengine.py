
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
    global camera_engine_thread
    if camera_engine_thread:
        aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_6X6_250)
        parameters = cv.aruco.DetectorParameters()
        detector = cv.aruco.ArucoDetector(aruco_dict, parameters)

        ret, frame = camera_engine_thread.cap.read()
        if ret:
            marker_corners, marker_ids, _ = detector.detectMarkers(frame)

            if marker_ids is not None:
                marker_ids_flat = marker_ids.flatten()
                required_ids = {1, 2, 3, 4}
                found_ids = set(marker_ids_flat)

                if required_ids.issubset(found_ids):
                    corners_dict = {id[0]: corner for id, corner in zip(marker_ids, marker_corners)}

                    try:
                        # Pick specific corners from each marker (adjust as needed)
                        pts1 = np.array([
                            corners_dict[1][0][0],  # top-left corner of marker 1
                            corners_dict[2][0][1],  # top-right corner of marker 2
                            corners_dict[4][0][2],  # bottom-right corner of marker 4
                            corners_dict[3][0][3],  # bottom-left corner of marker 3
                        ], dtype="float32")

                        # Destination square
                        size = 500
                        pts2 = np.array([
                            [0, 0],
                            [size - 1, 0],
                            [size - 1, size - 1],
                            [0, size - 1]
                        ], dtype="float32")

                        # Perspective transform
                        M = cv.getPerspectiveTransform(pts1, pts2)
                        warped = cv.warpPerspective(frame, M, (size, size))
                        _, buffer = cv.imencode('.png', warped)
                        return Response(content=buffer.tobytes(), media_type="image/png")

                    except KeyError as e:
                        print(f"Missing marker ID: {e}")
    return None
