"""
Natural Language to Mathematical Function Parser
Converts plain English descriptions to mathematical functions
"""

import re
import sympy as sp
from typing import Tuple, Optional, Dict
import numpy as np

class FunctionParser:
    """Parse natural language descriptions into mathematical functions"""
    
    def __init__(self):
        # Common mathematical terms mapping
        self.terms = {
            # Basic operations
            'plus': '+', 'minus': '-', 'times': '*', 'multiplied by': '*',
            'divided by': '/', 'over': '/', 'to the power of': '**', 'raised to': '**',
            'squared': '**2', 'cubed': '**3', 'square root': 'sqrt', 'cube root': '**(1/3)',
            
            # Trigonometric functions
            'sine': 'sin', 'cosine': 'cos', 'tangent': 'tan',
            'arcsine': 'asin', 'arccosine': 'acos', 'arctangent': 'atan',
            
            # Exponential and logarithmic
            'exponential': 'exp', 'natural log': 'log', 'logarithm': 'log',
            'log base': 'log', 'ln': 'log',
            
            # Variables
            'x': 'x', 'y': 'y', 't': 't',
            
            # Constants
            'pi': 'pi', 'e': 'E', 'infinity': 'oo',
        }
        
        # Function patterns for complex expressions
        self.patterns = {
            r'(\w+)\s+squared': r'\1**2',
            r'(\w+)\s+cubed': r'\1**3',
            r'(\w+)\s+to\s+the\s+(\d+)(?:st|nd|rd|th)\s+power': r'\1**\2',
            r'(\w+)\s+raised\s+to\s+the\s+(\d+)(?:st|nd|rd|th)\s+power': r'\1**\2',
            r'square\s+root\s+of\s+(\w+)': r'sqrt(\1)',
            r'cube\s+root\s+of\s+(\w+)': r'(\1)**(1/3)',
            r'(\d+)\s+times\s+(\w+)': r'\1*\2',
            r'(\w+)\s+times\s+(\d+)': r'\1*\2',
        }
    
    def parse_function(self, description: str) -> Tuple[bool, str, str, str]:
        """
        Parse mathematical function expression (e.g., "x^2 + 3x + 2")
        
        Returns:
            (success, parsed_function, function_type, latex_expression)
        """
        try:
            # Clean and normalize the description
            desc = description.strip()
            
            # Handle function notation like "f(x) = x^2 + 3x + 2"
            if '=' in desc:
                desc = desc.split('=')[1].strip()
            
            # Convert common mathematical notation
            desc = self._convert_mathematical_notation(desc)
            
            # Parse with SymPy
            x = sp.Symbol('x')
            expr = sp.sympify(desc)
            
            # Generate LaTeX
            latex_expr = sp.latex(expr)
            
            # Determine function type
            func_type = self._determine_function_type(expr)
            
            return True, str(expr), func_type, latex_expr
            
        except Exception as e:
            return False, "", "unknown", str(e)
    
    def _convert_mathematical_notation(self, desc: str) -> str:
        """Convert standard mathematical notation to Python/SymPy format"""
        
        # Replace ^ with ** for exponentiation
        desc = desc.replace('^', '**')
        
        # Handle parentheses multiplication (e.g., "(x+1)(x+2)" -> "(x+1)*(x+2)")
        desc = re.sub(r'\)\s*\(', ')*(', desc)
        
        # Handle implicit multiplication (e.g., "3x" -> "3*x", "x2" -> "x*2")
        # But preserve function names like sin, cos, exp, log, sqrt
        desc = re.sub(r'(\d+)([a-zA-Z])', r'\1*\2', desc)  # 3x -> 3*x
        desc = re.sub(r'([a-zA-Z])(\d+)', r'\1*\2', desc)  # x2 -> x*2
        
        # Handle common mathematical constants
        # Replace standalone constant e with E, but do not alter function names like exp
        desc = desc.replace('pi', 'pi')
        desc = re.sub(r'\be\b', 'E', desc)
        
        return desc
    
    def _determine_function_type(self, expr) -> str:
        """Determine the type of mathematical function"""
        expr_str = str(expr)
        
        if any(func in expr_str for func in ['sin', 'cos', 'tan', 'asin', 'acos', 'atan']):
            return 'trigonometric'
        elif any(func in expr_str for func in ['exp', 'log', 'ln']):
            return 'exponential_logarithmic'
        elif '**' in expr_str and not any(func in expr_str for func in ['sin', 'cos', 'tan', 'exp', 'log']):
            return 'polynomial'
        elif 'sqrt' in expr_str:
            return 'radical'
        else:
            return 'algebraic'
    
    def get_function_examples(self) -> Dict[str, list]:
        """Get examples of supported function descriptions"""
        return {
            'polynomial': [
                'x^2 + 2x - 1',
                'x^3 - 3x^2 + 2x',
                '2x^2 + 5x - 3',
                'x^4 - x^2 + 1'
            ],
            'trigonometric': [
                'sin(x)',
                'cos(x)',
                'tan(x)',
                'sin(x) + cos(x)',
                'sin(x)^2 + cos(x)^2'
            ],
            'exponential_logarithmic': [
                'exp(x)',
                'log(x)',
                'ln(x)',
                'exp(x) - log(x)',
                '2^x'
            ],
            'radical': [
                'sqrt(x)',
                'x^(1/3)',
                'sqrt(x) + 1',
                'sqrt(x^2 + 1)'
            ],
            'complex': [
                'sin(x) * exp(-x)',
                'x^2 * sin(x)',
                'exp(-x^2)',
                'log(x^2 + 1)'
            ]
        }

# Test the parser
if __name__ == "__main__":
    parser = FunctionParser()
    
    test_cases = [
        "x^2 + 2x - 1",
        "sin(x)",
        "exp(x)",
        "sqrt(x)",
        "x^3 - 3x^2 + 2x",
        "sin(x) * exp(-x)"
    ]
    
    print("Function Parser Test Results:")
    print("=" * 50)
    
    for desc in test_cases:
        success, func, func_type, latex = parser.parse_function(desc)
        print(f"Description: {desc}")
        print(f"Parsed: {func}")
        print(f"Type: {func_type}")
        print(f"LaTeX: {latex}")
        print(f"Success: {success}")
        print("-" * 30)
