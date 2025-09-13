import os
import time
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
import pyautogui
import cv2
import numpy as np
from PIL import Image
import uvicorn
from typing import Optional

app = FastAPI(title="Scrcpy Screenshot Server")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
WINDOW_TITLE = "SM-X610"

@app.get("/screenshot")
async def get_screenshot():
    """
    Capture a screenshot of the scrcpy window and return it as a PNG.
    """
    try:
        # Take screenshot of the entire screen
        screenshot = pyautogui.screenshot()
        
        # Verify the screenshot is not empty
        if not screenshot or screenshot.size[0] == 0 or screenshot.size[1] == 0:
            raise Exception("Screenshot capture resulted in an empty image")
    
        # Convert to OpenCV format
        frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # Encode as PNG
        _, buffer = cv2.imencode('.png', frame)
        
        # Return the image as a response
        return Response(
            content=buffer.tobytes(),
            media_type="image/png",
            headers={"Cache-Control": "no-cache"}
        )
        
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
