# Manim Animation Tool

A powerful tool for generating mathematical animations from standard mathematical expressions using Manim.

## 🎬 Features

- **Standard Mathematical Notation**: Input functions using standard math notation
- **Full Animation Features**: Coordinate axes, grids, labels, function equations
- **All Function Types**: Polynomials, trigonometric, exponential, logarithmic, radical
- **High-Quality Output**: MP4 animations with customizable quality
- **Local Storage**: Animations saved locally with automatic cleanup
- **RESTful API**: Easy integration with other services
- **Claude Integration**: Perfect for AI assistants

## 🚀 Quick Start

### 1. Start the Service
```bash
./start.sh
# or
uv run python main.py
```

### 2. Test the Service
```bash
python test_tool.py
```

### 3. API Documentation
Visit: http://localhost:8002/docs

## 📊 Supported Function Expressions

### Polynomial Functions
- `x^2 + 2x - 1`
- `x^3 - 3x^2 + 2x`
- `2x^2 + 5x - 3`
- `f(x) = x^4 - x^2 + 1`

### Trigonometric Functions
- `sin(x)`
- `cos(x)`
- `tan(x)`
- `sin(x) + cos(x)`

### Exponential & Logarithmic
- `exp(x)`
- `log(x)` or `ln(x)`
- `2^x`
- `exp(-x)`

### Radical Functions
- `sqrt(x)`
- `x^(1/3)`
- `sqrt(x) + 1`

### Complex Combinations
- `sin(x) * exp(-x)`
- `x^2 * sin(x)`
- `exp(-x^2)`

## 🔧 API Endpoints

### Generate Animation
```bash
POST /generate-animation
```

**Request:**
```json
{
  "function_description": "x^2 + 2x - 1",
  "domain": [-5, 5],
  "duration": 3.0,
  "quality": "medium",
  "show_grid": true,
  "show_axes": true,
  "show_labels": true
}
```

### Parse Function
```bash
POST /parse-function
```

**Request:**
```json
{
  "function_description": "sin(x)"
}
```

### Download Animation
```bash
GET /download/{animation_id}
```

### Get Examples
```bash
GET /examples
```

## 🎯 Usage Examples

### Basic Animation
```bash
curl -X POST http://localhost:8002/generate-animation \
  -H "Content-Type: application/json" \
  -d '{"function_description": "x^2", "domain": [-3, 3]}'
```

### Trigonometric Function
```bash
curl -X POST http://localhost:8002/generate-animation \
  -H "Content-Type: application/json" \
  -d '{"function_description": "sin(x)", "domain": [-10, 10], "duration": 4.0}'
```

### Complex Function
```bash
curl -X POST http://localhost:8002/generate-animation \
  -H "Content-Type: application/json" \
  -d '{"function_description": "exp(-x^2)", "domain": [-3, 3], "quality": "high"}'
```

## 🔗 Integration with Claude

Perfect for AI assistants! Claude can call this service to generate mathematical visualizations:

```python
def generate_math_animation(description: str, domain: list):
    response = requests.post("http://localhost:8002/generate-animation", json={
        "function_description": description,
        "domain": domain
    })
    return response.json()
```

## 📁 Project Structure

```
manim_tool/
├── main.py                 # FastAPI application
├── test_tool.py           # Test script
├── start.sh               # Start script
├── util/
│   ├── function_parser.py # Natural language parser
│   ├── manim_engine.py    # Manim animation engine
│   └── lib/
│       └── request.py     # Pydantic models
└── animations/            # Generated MP4 files
```

## ⚙️ Configuration

- **Port**: 8002 (configurable in main.py)
- **Output Directory**: `animations/`
- **Quality Options**: low, medium, high
- **Auto Cleanup**: Files older than 1 hour are automatically deleted

## 🛠️ Dependencies

- FastAPI - Web framework
- Manim - Mathematical animations
- SymPy - Symbolic mathematics
- NumPy - Numerical computing
- Pydantic - Data validation

## 📝 Notes

- Animations are rendered using Manim's high-quality engine
- All functions support basic calculus operations
- Natural language parsing handles common mathematical expressions
- MP4 files are saved locally for easy access
