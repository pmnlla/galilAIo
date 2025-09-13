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
        # Find the scrcpy window
        window = None
        try:
            window = pyautogui.getWindowsWithTitle(WINDOW_TITLE)[0]
        except IndexError:
            logger.error(f"Could not find window with title: {WINDOW_TITLE}")
            raise HTTPException(
                status_code=404,
                detail=f"Could not find window with title: {WINDOW_TITLE}"
            )
        
        # Activate the window
        window.activate()
        time.sleep(0.5)  # Give window time to come to foreground
        
        # Get window dimensions
        left, top, width, height = window.left, window.top, window.width, window.height
        
        # Take screenshot of the window
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        
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
        "screenshot_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
