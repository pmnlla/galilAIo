from vision.util.transformationkit.imagereworkengine import grab_camera_thread_capture
from vision.util.transformationkit.imagereworkengine import kill_camera_thread
from vision.util.transformationkit.imagereworkengine import init_camera_thread
from vision.util.transformationkit.imagereworkengine import aruco_marker_capture, position_correction_capture
from vision.util.lib.request import FiducialRequest, ImageRequest, CorrectionRequest
from typing import Union
import base64
import numpy as np
import cv2
import hashlib

from util import markergen

from fastapi import FastAPI, HTTPException, BackgroundTasks

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}



@app.get("/gen-marker")
def gen_marker(request: FiducialRequest):
    return markergen.marker_gen(request.position)


@app.post("/upload-image")
def upload_image(request: ImageRequest):
    try:
        # Remove data URL prefix if present (e.g., "data:image/png;base64,")
        image_data = request.image_data
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        # Decode base64 string
        image_bytes = base64.b64decode(image_data)
        
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        
        # Decode image using OpenCV
        image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image data")
        
        # Check if it's a PNG by trying to encode it back to PNG
        success, encoded_img = cv2.imencode('.png', image)
        if not success:
            # If encoding fails, it's not a valid PNG. Send back a hash of the file for verification.
            hash = hashlib.sha256(image_bytes).hexdigest()
            raise HTTPException(status_code=400, detail="Invalid image data. But we've got a sha256 hash, so you can check that the image arrived properly.Said hash: " + hash)
        
        # Get image info
        height, width = image.shape[:2]
        channels = image.shape[2] if len(image.shape) == 3 else 1
        
        return {
            "message": "PNG image received successfully",
            "image_info": {
                "width": width,
                "height": height,
                "channels": channels,
                "dtype": str(image.dtype),
                "size_bytes": len(image_bytes)
            }
        }
        
    except base64.binascii.Error:
        raise HTTPException(status_code=400, detail="Invalid base64 encoding")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")

@app.get("/start-image-engine")
def start_image_engine(background_tasks: BackgroundTasks):
    background_tasks.add_task(init_camera_thread)
    return "True"

@app.get("/kill-image-engine")
def kill_image_engine(background_tasks: BackgroundTasks):
    background_tasks.add_task(kill_camera_thread)
    return "True"

@app.get("/current-frame")
def get_current_frame():
    return grab_camera_thread_capture()

@app.get("/current-frame-aruco")
def get_aruco_frame():
    return aruco_marker_capture()

@app.get("/current-frame-correction")
def get_corrected_frame(request: CorrectionRequest):
    return position_correction_capture(request.threshold)