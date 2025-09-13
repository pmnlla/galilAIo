from typing import Union
import base64
import numpy as np
import cv2

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


class ImageRequest(BaseModel):
    image_data: str  # base64-encoded PNG


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
            raise HTTPException(status_code=400, detail="Image must be in PNG format")
        
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