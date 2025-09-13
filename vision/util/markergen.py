from numpy.random.mtrand import randint
from base64 import b64encode
import cv2
from fastapi.responses import Response
import random

mapping = {
    "LU": 1,
    "RU": 2,
    "LD": 3,
    "RD": 3
}

def marker_gen(pos: str) -> str:
    try:
        # cv::aruco::Dictionary dictionary = cv::aruco::getPredefinedDictionary(cv::aruco::DICT_6X6_250);
        img: cv2.mat = None
        dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        img = cv2.aruco.generateImageMarker(dict, mapping[pos], 200, img,)
        stat, buffer = cv2.imencode(".png", img)
        #if not stat:
        #    return "Failed to encode image. Try again :see_no_evil:"

        return Response(content=buffer.tobytes(), media_type="image/png")
        #return "worky"
    except:
        return "Misc failure"