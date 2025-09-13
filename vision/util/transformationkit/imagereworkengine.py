
import numpy as np
import cv2 as cv
import threading
from threading import Thread
from fastapi.responses import Response

from vision.util.autobrightness import automatic_brightness_and_contrast
from . import softbinary as sb

class cameraImageWorker(Thread):
    def __init__(self):
        super().__init__()  # Call the parent class's constructor
        self.should_stop = threading.Event()
        self.cap = None

    def run(self):
        self.cap = cv.VideoCapture(0)
        self.cap.set(cv.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, 1080)

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

def position_correction_capture(thres: int):
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

                        scale_factor = 2  # or 3, 4, etc.

                        output_width = int(1280 * scale_factor)
                        output_height = int(1280 * scale_factor)

                        # Scale destination points accordingly
                        pts2 = np.array([
                            [0, 0], 
                            [output_width - 1, 0],
                            [output_width - 1, output_height - 1],
                            [0, output_height - 1]
                        ], dtype="float32")

                        # Perspective transform
                        M = cv.getPerspectiveTransform(pts1, pts2)
                        warped = cv.warpPerspective(frame, M, (output_width, output_height), flags=cv.INTER_LINEAR)
                        # equalized = cv.equalizeHist(grayscale)
                        # 
                        brightness_contrast, a, b = automatic_brightness_and_contrast(warped)  
                        grayscale = cv.cvtColor(warped, cv.COLOR_BGR2GRAY)
                        # threshold = cv.threshold(grayscale, thres, 255, cv.THRESH_BINARY)[1]
                        #ret, otsu_thresh = cv.threshold(grayscale, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
                        #adaptive_mean_thresh = cv.adaptiveThreshold(img, 255,
                        #                        cv.ADAPTIVE_THRESH_MEAN_C,
                        #                        cv.THRESH_BINARY, 11, 2)
                        #   Apply adaptive Gaussian thresholding
                        # Apply adaptive thresholding using ADAPTIVE_THRESH_MEAN_C
                        #thresh_mean = cv.adaptiveThreshold(grayscale, 255, cv.ADAPTIVE_THRESH_MEAN_C,cv.THRESH_BINARY, 11, 2)
                        #thresh_gaussian = cv.adaptiveThreshold(grayscale, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C,
                         #               cv.THRESH_BINARY, 11, 2)
                        
                        #final = sb.combine_process(brightness_contrast, thresh_gaussian)

                        gamma = sb.adjust_gamma(warped, 1.2)
                        mask = sb.process_image(gamma)
                        final = sb.combine_process(warped, mask)


                        # Return the corrected image    
                        _, buffer = cv.imencode('.png', final)
                        return Response(content=buffer.tobytes(), media_type="image/png")

                    except KeyError as e:
                        print(f"Missing marker ID: {e}")
    return None
