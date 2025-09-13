"""
Simple Manim Animation Tool - Main FastAPI Application
Generates mathematical animations from standard mathematical expressions
"""

import os
import time
import asyncio
from pathlib import Path
from typing import Optional
import base64
import io
import uuid

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image
import uvicorn
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import rc
import sympy as sp

# Configure matplotlib
plt.style.use('dark_background')
rc('font', size=12)

from util.lib.request import AnimationRequest, AnimationResponse, FunctionParseRequest, FunctionParseResponse
from util.function_parser import FunctionParser

# Initialize FastAPI app
app = FastAPI(
    title="Manim Animation Tool",
    description="Generate mathematical animations from standard mathematical expressions",
    version="1.0.0"
)

# Initialize components
function_parser = FunctionParser()

# Output directory for animations
OUTPUT_DIR = Path("animations")
OUTPUT_DIR.mkdir(exist_ok=True)

class SimpleAnimator:
    """Simple animation generator using matplotlib"""
    
    @staticmethod
    def create_animation(
        function_description: str,
        domain: list,
        range_vals: Optional[list] = None,
        duration: float = 3.0,
        quality: str = "medium"
    ):
        """Create animation using matplotlib"""
        try:
            # Parse function
            success, parsed_func, func_type, latex_expr = function_parser.parse_function(function_description)
            if not success:
                return False, "", f"Failed to parse function: {parsed_func}"
            
            # Generate unique ID
            animation_id = str(uuid.uuid4())
            
            # Create figure
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Set domain
            ax.set_xlim(domain[0], domain[1])
            
            # Calculate y range
            y_min, y_max = SimpleAnimator._calculate_y_range(parsed_func, domain, range_vals)
            ax.set_ylim(y_min, y_max)
            
            # Set up plot
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0, color='white', linewidth=0.5)
            ax.axvline(x=0, color='white', linewidth=0.5)
            ax.set_xlabel('x', fontsize=14)
            ax.set_ylabel('f(x)', fontsize=14)
            ax.set_title(f'f(x) = {latex_expr}', fontsize=16, color='cyan')
            
            # Create function
            x_vals = np.linspace(domain[0], domain[1], 1000)
            x = sp.Symbol('x')
            expr = sp.sympify(parsed_func)
            func = sp.lambdify(x, expr, modules=['numpy', 'math'])
            
            # Initialize line
            line, = ax.plot([], [], 'yellow', linewidth=3)
            
            # Animation function
            def animate(frame):
                progress = min(frame / (duration * 30), 1.0)  # 30 fps
                end_idx = int(len(x_vals) * progress)
                
                if end_idx > 0:
                    x_show = x_vals[:end_idx]
                    try:
                        y_show = [func(x) for x in x_show if not (np.isnan(func(x)) or np.isinf(func(x)))]
                        if len(y_show) == len(x_show):
                            line.set_data(x_show, y_show)
                    except:
                        pass
                return line,
            
            # Create animation
            frames = int(duration * 30)
            anim = animation.FuncAnimation(
                fig, animate, frames=frames, interval=33, blit=True, repeat=True
            )
            
            # Save as GIF
            output_file = OUTPUT_DIR / f"{animation_id}.gif"
            anim.save(output_file, writer='pillow', fps=30, dpi=100)
            plt.close(fig)
            
            return True, animation_id, None
            
        except Exception as e:
            return False, "", str(e)
    
    @staticmethod
    def _calculate_y_range(parsed_func: str, domain: list, range_vals: Optional[list] = None):
        """Calculate appropriate y range"""
        if range_vals:
            return range_vals[0], range_vals[1]
        
        try:
            x_vals = np.linspace(domain[0], domain[1], 1000)
            x = sp.Symbol('x')
            expr = sp.sympify(parsed_func)
            func = sp.lambdify(x, expr, modules=['numpy', 'math'])
            
            y_vals = []
            for x_val in x_vals:
                try:
                    y_val = func(x_val)
                    if not (np.isnan(y_val) or np.isinf(y_val)):
                        y_vals.append(y_val)
                except:
                    continue
            
            if y_vals:
                y_min, y_max = min(y_vals), max(y_vals)
                y_range = y_max - y_min
                return y_min - 0.1 * y_range, y_max + 0.1 * y_range
            else:
                return -10, 10
        except:
            return -10, 10

@app.get("/")
def read_root():
    """Root endpoint with API information"""
    return {
        "service": "Manim Animation Tool",
        "version": "1.0.0",
        "description": "Generate mathematical animations from standard mathematical expressions",
        "endpoints": {
            "POST /generate-animation": "Generate mathematical animation",
            "POST /parse-function": "Test function parsing",
            "GET /download/{animation_id}": "Download generated animation",
            "GET /examples": "Get function examples",
            "GET /health": "Health check"
        },
        "example_request": {
            "function_description": "x^2 + 2x - 1",
            "domain": [-5, 5],
            "duration": 3.0,
            "quality": "medium"
        }
    }

@app.post("/generate-animation", response_model=AnimationResponse)
async def generate_animation(request: AnimationRequest, background_tasks: BackgroundTasks):
    """Generate a mathematical animation from standard mathematical expression"""
    try:
        # Generate animation
        success, animation_id, error = SimpleAnimator.create_animation(
            function_description=request.function_description,
            domain=request.domain,
            range_vals=request.range_vals,
            duration=request.duration,
            quality=request.quality
        )
        
        if not success:
            return AnimationResponse(
                animation_id=animation_id,
                status="error",
                message="Failed to generate animation",
                error=error
            )
        
        # Schedule cleanup
        background_tasks.add_task(_cleanup_old_files)
        
        return AnimationResponse(
            animation_id=animation_id,
            status="completed",
            message="Animation generated successfully",
            file_path=f"animations/{animation_id}.gif"
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
    """Download the generated animation file"""
    file_path = OUTPUT_DIR / f"{animation_id}.gif"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Animation not found")
    
    return FileResponse(
        path=file_path,
        filename=f"animation_{animation_id}.gif",
        media_type="image/gif"
    )

@app.get("/examples")
async def get_function_examples():
    """Get examples of supported function expressions"""
    examples = function_parser.get_function_examples()
    
    return {
        "message": "Supported function expressions",
        "examples": examples,
        "usage_tips": [
            "Use standard mathematical notation",
            "Examples: 'x^2 + 3x + 2', 'sin(x)', 'exp(x)'",
            "Supported operations: +, -, *, /, ^ (exponentiation)",
            "Supported functions: sin, cos, tan, exp, log, sqrt"
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
        "total_animations": len(list(OUTPUT_DIR.glob("*.gif")))
    }

async def _cleanup_old_files():
    """Clean up animation files older than 1 hour"""
    current_time = time.time()
    for file_path in OUTPUT_DIR.glob("*.gif"):
        if current_time - file_path.stat().st_mtime > 3600:  # 1 hour
            file_path.unlink()

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8002,
        reload=True
    )
