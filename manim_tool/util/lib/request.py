from pydantic import BaseModel, Field
from typing import List, Optional

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
