from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class AnimationRequest(BaseModel):
    """Request model for generating mathematical animations"""
    function_description: str = Field(..., description="Mathematical function expression (e.g., 'x^2 + 3x + 2', 'sin(x)', 'exp(x)', 'f(x) = x^3 - 2x + 1')")
    domain: List[float] = Field(..., description="Domain range [min, max] for the function")
    range_vals: Optional[List[float]] = Field(None, alias="range", description="Optional range values [min, max] for y-axis")
    duration: float = Field(default=3.0, description="Animation duration in seconds")
    quality: str = Field(default="medium", description="Video quality: low, medium, high")
    show_grid: bool = Field(default=True, description="Show coordinate grid")
    show_axes: bool = Field(default=True, description="Show coordinate axes")
    show_labels: bool = Field(default=True, description="Show axis labels and function equation")

class AnimationResponse(BaseModel):
    """Response model for animation generation"""
    animation_id: str
    status: str
    message: str
    file_path: Optional[str] = None
    error: Optional[str] = None
    preview_image: Optional[str] = None  # Base64 encoded preview

class FunctionParseRequest(BaseModel):
    """Request model for testing function parsing"""
    function_description: str = Field(..., description="Mathematical function expression (e.g., 'x^2 + 3x + 2', 'sin(x)', 'exp(x)')")

class FunctionParseResponse(BaseModel):
    """Response model for function parsing"""
    original_description: str
    parsed_function: str
    function_type: str
    latex_expression: str
    success: bool
    error: Optional[str] = None


class JSONAnimationOptions(BaseModel):
    """Options for JSON-driven animations"""
    sum_type: Optional[str] = Field(None, description="Riemann sum sampling: left or right")
    num_rectangles: Optional[int] = Field(None, description="Number of Riemann rectangles")
    point: Optional[float] = Field(None, description="Point for tangent in derivative scene")
    equations: Optional[List[str]] = Field(None, description="Equations for linear systems (e.g., 'y = 2*x + 1', '2*x + y = 5')")


class JSONAnimationRequest(BaseModel):
    """Request model matching the JSON-driven animator"""
    type: str = Field(..., description="Animation type: riemann_sum | derivative | integral | linear_system")
    function: Optional[str] = Field(None, description="Function expression for applicable types (e.g., 'x^2', 'sin(x)')")
    domain: List[float] = Field(..., description="Domain range [min, max] for x")
    options: Optional[JSONAnimationOptions] = Field(None, description="Additional options per animation type")
