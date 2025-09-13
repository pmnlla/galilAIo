"""
Manim Animation Tool - Main FastAPI Application
Generates mathematical animations from natural language descriptions
"""

import os
import time
import asyncio
from pathlib import Path
from typing import Optional
import base64
import io

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image
import uvicorn

from util.lib.request import (
    AnimationRequest,
    AnimationResponse,
    FunctionParseRequest,
    FunctionParseResponse,
    JSONAnimationRequest,
)
from util.function_parser import FunctionParser
from util.manim_engine import ManimAnimationEngine
from working_json_animator import create_working_animation_from_json

# Initialize FastAPI app
app = FastAPI(
    title="Manim Animation Tool",
    description="Generate mathematical animations from natural language descriptions using Manim",
    version="1.0.0"
)

# Initialize components
function_parser = FunctionParser()
animation_engine = ManimAnimationEngine()

# Output directory for animations
OUTPUT_DIR = Path("animations")
OUTPUT_DIR.mkdir(exist_ok=True)

@app.get("/")
def read_root():
    """Root endpoint with API information"""
    return {
        "service": "Manim Animation Tool",
        "version": "1.0.0",
        "description": "Generate mathematical animations from natural language descriptions",
        "endpoints": {
            "POST /generate-animation": "Generate mathematical animation",
            "POST /parse-function": "Test function parsing",
            "POST /generate-animation-json": "Generate animation from LLM-style JSON",
            "GET /download/{animation_id}": "Download generated animation",
            "GET /examples": "Get function examples",
            "GET /health": "Health check"
        },
        "example_request": {
            "type": "riemann_sum",
            "function": "x^2 + 2*x - 1",
            "domain": [0, 3],
            "options": {"sum_type": "right", "num_rectangles": 12}
        }
    }
@app.post("/generate-animation-json", response_model=AnimationResponse)
async def generate_animation_json(request: JSONAnimationRequest):
    """Generate an animation from LLM-style JSON (matches working JSON animator)."""
    try:
        req_dict = request.dict(by_alias=True)
        success, animation_id, file_path = create_working_animation_from_json(req_dict)
        if not success:
            return AnimationResponse(
                animation_id=animation_id,
                status="error",
                message="Failed to generate animation from JSON",
                error=file_path,
            )
        return AnimationResponse(
            animation_id=animation_id,
            status="completed",
            message="Animation generated successfully",
            file_path=file_path,
        )
    except Exception as e:
        return AnimationResponse(
            animation_id="",
            status="error",
            message="Internal server error",
            error=str(e),
        )

@app.post("/generate-animation", response_model=AnimationResponse)
async def generate_animation(request: AnimationRequest, background_tasks: BackgroundTasks):
    """Generate a mathematical animation from natural language description"""
    try:
        # Parse and validate the function
        success, parsed_func, func_type, latex_expr = function_parser.parse_function(request.function_description)
        if not success:
            return AnimationResponse(
                animation_id="",
                status="error",
                message="Failed to parse function description",
                error=parsed_func
            )
        
        # Generate animation
        success, animation_id, error = animation_engine.create_animation(
            function_description=request.function_description,
            domain=request.domain,
            range_vals=request.range_vals,
            duration=request.duration,
            quality=request.quality,
            show_grid=request.show_grid,
            show_axes=request.show_axes,
            show_labels=request.show_labels
        )
        
        if not success:
            return AnimationResponse(
                animation_id=animation_id,
                status="error",
                message="Failed to generate animation",
                error=error
            )
        
        # Create preview image (placeholder for now)
        preview_image = _create_preview_image(parsed_func, request.domain)
        
        # Schedule cleanup
        background_tasks.add_task(_cleanup_old_files)
        
        return AnimationResponse(
            animation_id=animation_id,
            status="completed",
            message="Animation generated successfully",
            file_path=f"animations/{animation_id}.mp4",
            preview_image=preview_image
        )
        
    except Exception as e:
        return AnimationResponse(
            animation_id="",
            status="error",
            message="Internal server error",
            error=str(e)
        )

@app.post("/parse-function", response_model=FunctionParseResponse)
async def parse_function(request: FunctionParseRequest):
    """Test function parsing without generating animation"""
    try:
        success, parsed_func, func_type, latex_expr = function_parser.parse_function(request.function_description)
        
        if success:
            return FunctionParseResponse(
                original_description=request.function_description,
                parsed_function=parsed_func,
                function_type=func_type,
                latex_expression=latex_expr,
                success=True
            )
        else:
            return FunctionParseResponse(
                original_description=request.function_description,
                parsed_function="",
                function_type="unknown",
                latex_expression="",
                success=False,
                error=parsed_func
            )
            
    except Exception as e:
        return FunctionParseResponse(
            original_description=request.function_description,
            parsed_function="",
            function_type="unknown",
            latex_expression="",
            success=False,
            error=str(e)
        )

@app.get("/download/{animation_id}")
async def download_animation(animation_id: str):
    """Download the generated animation MP4 file"""
    # Look in the actual output directory where Manim saves files
    media_dir = Path("media/videos/720p30")
    
    # Try to find the file with the animation_id in the filename
    matching_files = list(media_dir.glob(f"*{animation_id}.mp4"))
    
    if not matching_files:
        raise HTTPException(status_code=404, detail="Animation not found")
    
    file_path = matching_files[0]  # Use the first matching file
    
    return FileResponse(
        path=file_path,
        filename=f"animation_{animation_id}.mp4",
        media_type="video/mp4"
    )

@app.get("/examples")
async def get_function_examples():
    """Get examples of supported function descriptions"""
    examples = function_parser.get_function_examples()
    
    return {
        "message": "Supported function descriptions",
        "examples": examples,
        "usage_tips": [
            "Use plain English to describe mathematical functions",
            "Examples: 'x squared plus two x minus one', 'sine of x', 'exponential of x'",
            "Supported operations: plus, minus, times, divided by, squared, cubed, to the power of",
            "Supported functions: sine, cosine, tangent, exponential, natural log, square root"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "manim-animation-tool",
        "timestamp": time.time(),
        "output_directory": str(OUTPUT_DIR),
        "total_animations": len(list(OUTPUT_DIR.glob("*.mp4")))
    }

async def _cleanup_old_files():
    """Clean up animation files older than 1 hour"""
    current_time = time.time()
    for file_path in OUTPUT_DIR.glob("*.mp4"):
        if current_time - file_path.stat().st_mtime > 3600:  # 1 hour
            file_path.unlink()

def _create_preview_image(parsed_function: str, domain: list) -> str:
    """Create a preview image (placeholder implementation)"""
    try:
        # This would create an actual preview image
        # For now, return a placeholder
        return "preview_placeholder_base64"
    except:
        return ""

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,  # Different port from other services
        reload=True
    )
