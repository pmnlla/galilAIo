"""
Working JSON-Driven Mathematical Animation Generator
Fixed version that actually creates working animations
"""

import json
import uuid
import numpy as np
import sympy as sp
from pathlib import Path
from typing import Dict, Any, List
from manim import *
from util.function_parser import FunctionParser

import traceback

def create_working_animation_from_json(json_input: Dict[str, Any]) -> tuple[bool, str, str]:
    """
    Create working animation from JSON input
    
    Expected JSON format:
    {
        "type": "riemann_sum" | "derivative" | "linear_system",
        "function": "x^2",
        "domain": [0, 2],
        "options": {
            "sum_type": "left" | "right",
            "num_rectangles": 8,
            "point": 1.0,
            "equations": ["y = 2x + 1", "y = -x + 4"]
        }
    }
    """
    
    try:
        animation_type = json_input.get("type", "riemann_sum")
        function = json_input.get("function", "x^2")
        domain = json_input.get("domain", [0, 2])
        options = json_input.get("options", {})
        
        # Generate unique ID
        animation_id = str(uuid.uuid4())[:8]
        
        if animation_type == "riemann_sum":
            return _create_working_riemann_sum(function, domain, options, animation_id)
        elif animation_type == "derivative":
            return _create_working_derivative(function, domain, options, animation_id)
        elif animation_type == "linear_system":
            if options:
                equations = options.get("equations", ["y = 2*x + 1", "y = -x + 4"])
            else:
                equations = ["y=2*x+1","y=-x+4"]
            return _create_working_linear_system(equations, domain, animation_id)
        elif animation_type == "integral":
            return _create_working_integral(function, domain, options, animation_id)
        elif animation_type in ("equation", "equation_display"):
            equations = options.get("equations") if options else None
            # Fallback: if only a single function/equation string is provided
            if not equations and function:
                equations = [function]
            if not equations:
                return False, "", "No equations provided for equation display"
            return _create_working_equation_display(equations, animation_id)
        else:
            return False, "", f"Unknown animation type: {animation_type}"
            
    except Exception as e:
        print(traceback.format_exc())
        return False, "", str(e)

def _create_working_riemann_sum(function: str, domain: List[float], options: Dict[str, Any], animation_id: str) -> tuple[bool, str, str]:
    """Create working Riemann sum animation"""
    # Resolve options in outer scope so we can use them for naming/output
    sum_type = options.get("sum_type", "right")
    num_rectangles = options.get("num_rectangles", 8)

    class WorkingRiemannScene(Scene):
        def construct(self):
            # Parse function
            parser = FunctionParser()
            success, parsed_func, func_type, latex_expr = parser.parse_function(function)
            
            if not success:
                error_text = Text(f"Error: {parsed_func}", font_size=24, color=RED)
                self.add(error_text)
                self.wait(2)
                return
            
            # Calculate y range
            x_vals = np.linspace(domain[0], domain[1], 100)
            x = sp.Symbol('x')
            expr = sp.sympify(parsed_func)
            func = sp.lambdify(x, expr, modules=['numpy', 'math'])
            
            y_vals = [func(x_val) for x_val in x_vals if not (np.isnan(func(x_val)) or np.isinf(func(x_val)))]
            y_min, y_max = min(y_vals), max(y_vals)
            y_range = [y_min - 0.2 * (y_max - y_min), y_max + 0.2 * (y_max - y_min), (y_max - y_min) / 10]
            
            # Set up axes
            ax = Axes(
                x_range=[domain[0], domain[1], (domain[1] - domain[0]) / 10],
                y_range=y_range,
                axis_config={'include_tip': True},
            )
            
            # Plot the function
            curve = ax.plot(lambda x: func(x), color=BLUE, stroke_width=3)
            
            # Create Riemann rectangles
            dx = (domain[1] - domain[0]) / num_rectangles
            riemann_rects = ax.get_riemann_rectangles(
                curve,
                x_range=domain,
                dx=dx,
                input_sample_type=sum_type,
                stroke_width=1,
                fill_opacity=0.7,
                color=GREEN,
            )
            
            # Add title
            title = Text(f'{sum_type.title()} Riemann Sum: f(x) = {function}', 
                       font_size=24, color=WHITE)
            title.to_edge(UP)
            
            rect_info = Text(f'n = {num_rectangles} rectangles', font_size=16, color=BLUE)
            rect_info.next_to(title, DOWN)
            
            # Animation sequence
            self.play(Write(title))
            self.play(Write(rect_info))
            self.play(Create(ax))
            self.play(Create(curve), run_time=2)
            self.play(Create(riemann_rects), run_time=3)
            self.wait(2)
    
    # Configure and render (use Manim's default output system)
    config.quality = "medium_quality"
    # Sanitize filename for filesystem
    safe_function = function.replace('^', '_pow_').replace('/', '_').replace(' ', ' ')
    config.output_file = f"riemann_{sum_type}_{safe_function}_{animation_id}"
    
    scene = WorkingRiemannScene()
    scene.render()
    
    # Find the actual output file
    output_dir = Path("media/videos/720p30")
    output_files = list(output_dir.glob(f"riemann_{sum_type}_{safe_function}_{animation_id}*"))
    
    if output_files:
        return True, animation_id, str(output_files[0])
    else:
        return False, animation_id, "Output file not found"

def _create_working_derivative(function: str, domain: List[float], options: Dict[str, Any], animation_id: str) -> tuple[bool, str, str]:
    """Create working derivative animation"""
    
    class WorkingDerivativeScene(Scene):
        def construct(self):
            # Parse function
            parser = FunctionParser()
            success, parsed_func, func_type, latex_expr = parser.parse_function(function)
            
            if not success:
                error_text = Text(f"Error: {parsed_func}", font_size=24, color=RED)
                self.add(error_text)
                self.wait(2)
                return
            
            # Get point for tangent line
            point = options.get("point", (domain[0] + domain[1]) / 2)
            
            # Set up axes
            ax = Axes(
                x_range=[domain[0], domain[1], (domain[1] - domain[0]) / 10],
                y_range=[-10, 10, 2],
                axis_config={'include_tip': True},
            )
            
            # Create function and derivative
            x = sp.Symbol('x')
            expr = sp.sympify(parsed_func)
            func = sp.lambdify(x, expr, modules=['numpy', 'math'])
            
            derivative = sp.diff(expr, x)
            # Use sympy and numpy printers; allow non-strict to handle composite forms
            derivative_func = sp.lambdify(x, derivative, modules=['numpy', {'sin': np.sin, 'cos': np.cos, 'tan': np.tan, 'exp': np.exp, 'log': np.log, 'sqrt': np.sqrt}], dummify=False)
            
            # Plot the function and derivative
            curve = ax.plot(lambda x: func(x), color=BLUE, stroke_width=3)
            derivative_curve = ax.plot(lambda x: derivative_func(x), color=RED, stroke_width=2)
            
            # Calculate tangent line
            slope = derivative_func(point)
            y_intercept = func(point) - slope * point
            tangent_line = ax.plot(lambda x_val: slope * x_val + y_intercept, color=YELLOW, stroke_width=2)
            
            # Mark the point
            point_dot = Dot(ax.c2p(point, func(point)), color=YELLOW, radius=0.1)
            
            # Add title
            title = Text(f'Derivative: f(x) = {function}', font_size=24, color=WHITE)
            title.to_edge(UP)
            
            derivative_text = Text(f"f'(x) = {sp.latex(derivative)}", font_size=18, color=RED)
            derivative_text.next_to(title, DOWN)
            
            # Animation sequence
            self.play(Write(title))
            self.play(Write(derivative_text))
            self.play(Create(ax))
            self.play(Create(curve), run_time=2)
            self.play(Create(derivative_curve), run_time=2)
            self.play(Create(point_dot))
            self.play(Create(tangent_line), run_time=1)
            self.wait(2)
    
    # Configure and render
    config.quality = "medium_quality"
    safe_function = function.replace('^', '_pow_').replace('/', '_').replace(' ', ' ')
    config.output_file = f"derivative_{safe_function}_{animation_id}"
    
    scene = WorkingDerivativeScene()
    scene.render()
    
    # Find the actual output file
    output_dir = Path("media/videos/720p30")
    output_files = list(output_dir.glob(f"derivative_{safe_function}_{animation_id}*"))
    
    if output_files:
        return True, animation_id, str(output_files[0])
    else:
        return False, animation_id, "Output file not found"

def _create_working_linear_system(equations: List[str], domain: List[float], animation_id: str) -> tuple[bool, str, str]:
    """Create working linear system animation"""
    
    class WorkingLinearSystemScene(Scene):
        def construct(self):
            # Set up axes
            ax = Axes(
                x_range=[domain[0], domain[1], (domain[1] - domain[0]) / 10],
                y_range=[domain[0], domain[1], (domain[1] - domain[0]) / 10],
                axis_config={'include_tip': True},
            )
            
            # Parse equations and create lines
            lines = []
            colors = [BLUE, RED, GREEN, YELLOW, PURPLE]
            
            for i, equation in enumerate(equations):
                try:
                    # Parse equation: support explicit y=..., implicit ax+by=c
                    if '=' in equation:
                        left, right = equation.split('=')
                        x_sym = sp.Symbol('x')
                        y_sym = sp.Symbol('y')
                        
                        if 'y' in left and 'x' not in left:
                            # Explicit form: y = f(x)
                            y_expr = sp.sympify(right)
                            func = sp.lambdify(x_sym, y_expr, modules=['numpy', 'math'])
                            color = colors[i % len(colors)]
                            line = ax.plot(lambda x: func(x), color=color, stroke_width=2)
                            lines.append((line, equation, color))
                        else:
                            # Implicit form: ax + by = c or ax + by + c = 0
                            expr = sp.sympify(left) - sp.sympify(right)
                            try:
                                y_expr = sp.solve(expr, y_sym)[0]
                                func = sp.lambdify(x_sym, y_expr, modules=['numpy', 'math'])
                                color = colors[i % len(colors)]
                                line = ax.plot(lambda x: func(x), color=color, stroke_width=2)
                                lines.append((line, equation, color))
                            except Exception:
                                pass
                            
                except Exception as e:
                    continue
            
            # Add title
            title = Text('System of Linear Equations', font_size=24, color=WHITE)
            title.to_edge(UP)
            
            # Add equations
            equation_texts = VGroup()
            for i, (line, equation, color) in enumerate(lines):
                eq_text = Text(f'{i+1}. {equation}', color=color, font_size=16)
                equation_texts.add(eq_text)
            
            equation_texts.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
            equation_texts.next_to(title, DOWN, buff=0.5)
            equation_texts.to_edge(LEFT)
            
            # Animation sequence
            self.play(Write(title))
            self.play(Write(equation_texts))
            self.play(Create(ax))
            
            for line, equation, color in lines:
                self.play(Create(line), run_time=1.5)
            
            # Mark intersections if there are at least two lines
            if len(lines) >= 2:
                x_sym = sp.Symbol('x')
                y_sym = sp.Symbol('y')
                eq_exprs = []
                for _, eq_text, _ in lines:
                    left, right = eq_text.split('=')
                    expr = sp.sympify(left) - sp.sympify(right)
                    eq_exprs.append(expr)
                try:
                    sol = sp.solve((eq_exprs[0], eq_exprs[1]), (x_sym, y_sym), dict=True)
                    if sol:
                        sx = float(sol[0][x_sym])
                        sy = float(sol[0][y_sym])
                        dot = Dot(ax.c2p(sx, sy), color=YELLOW)
                        self.play(Create(dot))
                except Exception:
                    pass
            
            self.wait(2)
    
    # Configure and render
    config.quality = "medium_quality"
    config.output_file = f"linear_system_{len(equations)}_eqs_{animation_id}"
    
    scene = WorkingLinearSystemScene()
    scene.render()
    
    # Find the actual output file
    output_dir = Path("media/videos/720p30")
    output_files = list(output_dir.glob(f"linear_system_{len(equations)}_eqs_{animation_id}*"))
    
    if output_files:
        return True, animation_id, str(output_files[0])
    else:
        return False, animation_id, "Output file not found"

def _create_working_integral(function: str, domain: List[float], options: Dict[str, Any], animation_id: str) -> tuple[bool, str, str]:
    """Create working integral (area under curve) animation"""

    class WorkingIntegralScene(Scene):
        def construct(self):
            # Parse function
            parser = FunctionParser()
            success, parsed_func, func_type, latex_expr = parser.parse_function(function)
            if not success:
                error_text = Text(f"Error: {parsed_func}", font_size=24, color=RED)
                self.add(error_text)
                self.wait(2)
                return

            # Build function
            x = sp.Symbol('x')
            expr = sp.sympify(parsed_func)
            func = sp.lambdify(x, expr, modules=['numpy', 'math'])

            # Estimate y-range
            x_vals = np.linspace(domain[0], domain[1], 200)
            y_vals: List[float] = []
            for xv in x_vals:
                try:
                    yv = func(xv)
                    if not (np.isnan(yv) or np.isinf(yv)):
                        y_vals.append(float(yv))
                except Exception:
                    pass
            if not y_vals:
                y_vals = [-1.0, 1.0]
            y_min, y_max = min(y_vals), max(y_vals)
            pad = 0.2 * max(1e-6, (y_max - y_min))
            y_range = [y_min - pad, y_max + pad, max(0.1, (y_max - y_min) / 10.0)]

            # Axes
            ax = Axes(
                x_range=[domain[0], domain[1], (domain[1] - domain[0]) / 10],
                y_range=y_range,
                axis_config={'include_tip': True},
            )

            # Plot curve and area
            curve = ax.plot(lambda xv: func(xv), color=BLUE, stroke_width=3)
            area = ax.get_area(curve, x_range=domain, color=GREEN, opacity=0.5)

            # Compute definite integral
            try:
                integral_val = sp.integrate(expr, (x, domain[0], domain[1])).evalf()
                info_text = Text(f"∫_{domain[0]}^{domain[1]} f(x) dx ≈ {float(integral_val):.4f}", font_size=18, color=YELLOW)
            except Exception:
                info_text = Text(f"Area under f(x) on [{domain[0]}, {domain[1]}]", font_size=18, color=YELLOW)

            title = Text(f"Integral of f(x) = {function}", font_size=24, color=WHITE).to_edge(UP)
            info_text.next_to(title, DOWN)

            # Animate
            self.play(Write(title))
            self.play(Write(info_text))
            self.play(Create(ax))
            self.play(Create(curve), run_time=2)
            self.play(Create(area), run_time=2)
            self.wait(2)

    # Render
    config.quality = "medium_quality"
    safe_function = function.replace('^', '_pow_').replace('/', '_').replace(' ', ' ')
    config.output_file = f"integral_{safe_function}_{animation_id}"
    scene = WorkingIntegralScene()
    scene.render()
    output_dir = Path("media/videos/720p30")
    output_files = list(output_dir.glob(f"integral_{safe_function}_{animation_id}*"))
    if output_files:
        return True, animation_id, str(output_files[0])
    return False, animation_id, "Output file not found"

def _create_working_equation_display(equations: List[str], animation_id: str) -> tuple[bool, str, str]:
    """Display one or more equations using LaTeX (MathTex) with simple animations."""

    class WorkingEquationScene(Scene):
        def construct(self):
            title = Text("Equations", font_size=24, color=WHITE).to_edge(UP)
            self.play(Write(title))

            items: List[Mobject] = []
            for eq in equations:
                try:
                    # Allow raw LaTeX or simple strings; wrap if needed
                    tex = MathTex(eq) if any(ch in eq for ch in ['\\', '^', '_', '{', '}', '=', '+', '-', '*']) else MathTex(eq)
                    items.append(tex)
                except Exception:
                    items.append(Text(eq, font_size=24))

            group = VGroup(*items).arrange(DOWN, center=False, aligned_edge=LEFT, buff=0.5)
            group.next_to(title, DOWN, buff=0.75)
            group.to_edge(LEFT)

            for item in items:
                self.play(Write(item))
                self.wait(0.2)

            self.wait(1.5)

    config.quality = "medium_quality"
    config.output_file = f"equation_display_{animation_id}"
    scene = WorkingEquationScene()
    scene.render()
    output_dir = Path("media/videos/720p30")
    output_files = list(output_dir.glob(f"equation_display_{animation_id}*"))
    if output_files:
        return True, animation_id, str(output_files[0])
    return False, animation_id, "Output file not found"

def test_working_json_animator():
    """Test the working JSON animator"""
    print("🎬 Testing Working JSON-Driven Mathematical Animator...")
    
    # Test 1: Simple Riemann sum
    riemann_json = {
        "type": "riemann_sum",
        "function": "x^2",
        "domain": [0, 2],
        "options": {
            "sum_type": "right",
            "num_rectangles": 8
        }
    }
    
    print("\n1️⃣ Creating Riemann Sum from JSON...")
    print(f"   Input: {json.dumps(riemann_json, indent=2)}")
    success, anim_id, file_path = create_working_animation_from_json(riemann_json)
    if success:
        print(f"   ✅ Created: {file_path}")
    else:
        print(f"   ❌ Failed: {anim_id}")
    
    # Test 2: Derivative
    derivative_json = {
        "type": "derivative",
        "function": "x^3 - 3*x",
        "domain": [-3, 3],
        "options": {
            "point": 1.0
        }
    }
    
    print("\n2️⃣ Creating Derivative from JSON...")
    print(f"   Input: {json.dumps(derivative_json, indent=2)}")
    success, anim_id, file_path = create_working_animation_from_json(derivative_json)
    if success:
        print(f"   ✅ Created: {file_path}")
    else:
        print(f"   ❌ Failed: {anim_id}")

if __name__ == "__main__":
    test_working_json_animator()
