#!/bin/bash

# Start the Manim Animation Tool

echo "🎬 Starting Manim Animation Tool..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install uv first."
    exit 1
fi

# Create animations directory
mkdir -p animations

# Start the service
echo "🚀 Starting animation service on port 8002..."
echo "📖 API docs available at: http://localhost:8002/docs"
echo "🔍 Health check at: http://localhost:8002/health"
echo "🎯 Test the service with: python test_tool.py"

uv run python main.py
