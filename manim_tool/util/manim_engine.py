"""
Manim Animation Engine
Generates mathematical function animations with full features
"""

import os
import uuid
import numpy as np
import sympy as sp
from pathlib import Path
from typing import Tuple, Optional
import base64
import io

from manim import *
from .function_parser import FunctionParser

# Configure Manim for high-quality output
config.quality = "high_quality"
config.output_file = "animation"
config.pixel_width = 1920
config.pixel_height = 1080
config.frame_rate = 30

class ManimAnimationEngine:
    """Engine for creating mathematical animations using Manim"""
    
    def __init__(self, output_dir: str = "animations"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.parser = FunctionParser()
    
    def create_animation(
        self,
        function_description: str,
        domain: list,
        range_vals: Optional[list] = None,
        duration: float = 3.0,
        quality: str = "medium",
        show_grid: bool = True,
        show_axes: bool = True,
        show_labels: bool = True
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Create a mathematical function animation
        
        Returns:
            (success, animation_id, error_message)
        """
        try:
            # Parse the function
            success, parsed_func, func_type, latex_expr = self.parser.parse_function(function_description)
            if not success:
                return False, "", f"Failed to parse function: {parsed_func}"
            
            # Generate unique animation ID
            animation_id = str(uuid.uuid4())
            
            # Set output file
            config.output_file = animation_id
            
            # Configure quality
            self._configure_quality(quality)
            
            # Create and render the scene
            scene = FunctionAnimationScene(
                function_description=function_description,
                parsed_function=parsed_func,
                function_type=func_type,
                latex_expression=latex_expr,
                domain=domain,
                range_vals=range_vals,
                duration=duration,
                show_grid=show_grid,
                show_axes=show_axes,
                show_labels=show_labels
            )
            
            # Render the animation
            scene.render()
            
            # Move the output file to our directory
            output_file = self.output_dir / f"{animation_id}.mp4"
            if (Path.cwd() / "media" / "videos" / f"{animation_id}" / f"{quality}" / f"{animation_id}.mp4").exists():
                source_file = Path.cwd() / "media" / "videos" / f"{animation_id}" / f"{quality}" / f"{animation_id}.mp4"
                source_file.rename(output_file)
            
            return True, animation_id, None
            
        except Exception as e:
            return False, "", str(e)
    
    def _configure_quality(self, quality: str):
        """Configure Manim quality settings"""
        if quality == "low":
            config.pixel_width = 854
            config.pixel_height = 480
            config.frame_rate = 24
        elif quality == "medium":
            config.pixel_width = 1280
            config.pixel_height = 720
            config.frame_rate = 30
        else:  # high
            config.pixel_width = 1920
            config.pixel_height = 1080
            config.frame_rate = 30

class FunctionAnimationScene(Scene):
    """Manim scene for animating mathematical functions"""
    
    def __init__(self, **kwargs):
        super().__init__()
        self.function_description = kwargs.get('function_description', '')
        self.parsed_function = kwargs.get('parsed_function', '')
        self.function_type = kwargs.get('function_type', '')
        self.latex_expression = kwargs.get('latex_expression', '')
        self.domain = kwargs.get('domain', [-5, 5])
        self.range_vals = kwargs.get('range_vals', None)
        self.duration = kwargs.get('duration', 3.0)
        self.show_grid = kwargs.get('show_grid', True)
        self.show_axes = kwargs.get('show_axes', True)
        self.show_labels = kwargs.get('show_labels', True)
    
    def construct(self):
        """Main animation construction"""
        # Create coordinate system
        axes = self._create_axes()
        
        # Create function graph
        graph = self._create_function_graph(axes)
        
        # Create labels and annotations
        labels = self._create_labels(axes)
        
        # Animation sequence
        self._animate_sequence(axes, graph, labels)
    
    def _create_axes(self):
        """Create coordinate axes with grid"""
        # Determine y range
        y_min, y_max = self._calculate_y_range()
        
        # Create axes
        axes = Axes(
            x_range=[self.domain[0], self.domain[1], (self.domain[1] - self.domain[0]) / 10],
            y_range=[y_min, y_max, (y_max - y_min) / 10],
            x_length=12,
            y_length=8,
            axis_config={"color": BLUE, "stroke_width": 2},
            x_axis_config={
                "numbers_to_include": np.arange(self.domain[0], self.domain[1] + 1, max(1, (self.domain[1] - self.domain[0]) // 5)),
                "font_size": 24,
                "decimal_number_config": {"num_decimal_places": 0}
            },
            y_axis_config={
                "numbers_to_include": np.arange(y_min, y_max + 1, max(1, (y_max - y_min) // 5)),
                "font_size": 24,
                "decimal_number_config": {"num_decimal_places": 0}
            },
            tips=False,
        )
        
        # Add grid if requested
        if self.show_grid:
            axes.add_coordinates()
        
        return axes
    
    def _create_function_graph(self, axes):
        """Create the function graph"""
        try:
            # Convert parsed function to lambda
            x = sp.Symbol('x')
            expr = sp.sympify(self.parsed_function)
            func = sp.lambdify(x, expr, modules=['numpy', 'math'])
            
            # Create graph
            graph = axes.plot(
                func,
                color=YELLOW,
                x_range=[self.domain[0], self.domain[1]],
                stroke_width=4
            )
            
            return graph
            
        except Exception as e:
            # Fallback: create a simple line if function fails
            return axes.plot(lambda x: 0, color=YELLOW, x_range=[self.domain[0], self.domain[1]])
    
    def _create_labels(self, axes):
        """Create labels and annotations"""
        labels = VGroup()
        
        if self.show_labels:
            # Axis labels
            x_label = axes.get_x_axis_label("x", edge=DOWN, direction=DOWN, buff=0.5)
            y_label = axes.get_y_axis_label("f(x)", edge=LEFT, direction=LEFT, buff=0.5)
            labels.add(x_label, y_label)
            
            # Function equation
            if self.latex_expression:
                equation = MathTex(f"f(x) = {self.latex_expression}", font_size=36)
                equation.set_color(CYAN)
                equation.to_corner(UL, buff=1)
                labels.add(equation)
            
            # Function description
            description = Text(self.function_description, font_size=24)
            description.set_color(WHITE)
            description.next_to(equation, DOWN, aligned_edge=LEFT)
            labels.add(description)
        
        return labels
    
    def _animate_sequence(self, axes, graph, labels):
        """Create the animation sequence"""
        # 1. Show axes
        if self.show_axes:
            self.play(Create(axes), run_time=1)
        
        # 2. Show labels
        if self.show_labels and labels:
            self.play(Write(labels), run_time=1)
        
        # 3. Animate function drawing
        self.play(Create(graph), run_time=self.duration - 2)
        
        # 4. Hold final frame
        self.wait(1)
    
    def _calculate_y_range(self):
        """Calculate appropriate y range for the function"""
        if self.range_vals:
            return self.range_vals[0], self.range_vals[1]
        
        try:
            # Sample function values to determine range
            x_vals = np.linspace(self.domain[0], self.domain[1], 1000)
            x = sp.Symbol('x')
            expr = sp.sympify(self.parsed_function)
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

# Test the engine
if __name__ == "__main__":
    engine = ManimAnimationEngine()
    
    # Test with a simple function
    success, anim_id, error = engine.create_animation(
        function_description="x squared plus two x minus one",
        domain=[-5, 5],
        duration=3.0
    )
    
    print(f"Success: {success}")
    print(f"Animation ID: {anim_id}")
    print(f"Error: {error}")
