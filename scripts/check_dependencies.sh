#!/bin/bash
# Check system dependencies for The Mixer

echo "Checking system dependencies for The Mixer..."
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Track if all dependencies are met
ALL_OK=true

# Check ffmpeg
echo -n "Checking ffmpeg... "
if command_exists ffmpeg; then
    VERSION=$(ffmpeg -version | head -n1)
    echo "✓ Found: $VERSION"
else
    echo "✗ NOT FOUND"
    echo "  Install: sudo apt-get install ffmpeg  (Ubuntu/Debian)"
    echo "           brew install ffmpeg           (macOS)"
    ALL_OK=false
fi

# Check Python
echo -n "Checking Python... "
if command_exists python3; then
    VERSION=$(python3 --version)
    echo "✓ Found: $VERSION"

    # Check Python version >= 3.9
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if (( $(echo "$PYTHON_VERSION >= 3.9" | bc -l) )); then
        echo "  Version OK (>= 3.9)"
    else
        echo "  ✗ Version too old (need >= 3.9, have $PYTHON_VERSION)"
        ALL_OK=false
    fi
else
    echo "✗ NOT FOUND"
    ALL_OK=false
fi

# Check pip
echo -n "Checking pip... "
if command_exists pip3; then
    VERSION=$(pip3 --version)
    echo "✓ Found: $VERSION"
else
    echo "✗ NOT FOUND"
    echo "  Install: python3 -m ensurepip"
    ALL_OK=false
fi

# Check libsndfile (via pkg-config)
echo -n "Checking libsndfile... "
if pkg-config --exists sndfile 2>/dev/null; then
    VERSION=$(pkg-config --modversion sndfile)
    echo "✓ Found: v$VERSION"
else
    echo "⚠ Cannot verify (pkg-config not available or libsndfile not found)"
    echo "  Install: sudo apt-get install libsndfile1  (Ubuntu/Debian)"
    echo "           brew install libsndfile           (macOS)"
    echo "  Note: May already be installed even if not detected"
fi

# Optional: Check for CUDA (GPU acceleration)
echo ""
echo "Optional dependencies:"
echo -n "Checking CUDA... "
if command_exists nvcc; then
    VERSION=$(nvcc --version | grep release | sed 's/.*release //' | sed 's/,.*//')
    echo "✓ Found: v$VERSION (GPU acceleration available)"
else
    echo "⚠ NOT FOUND (will use CPU - slower but functional)"
fi

echo ""
if [ "$ALL_OK" = true ]; then
    echo "✓ All required dependencies are installed!"
    echo ""
    echo "Next steps:"
    echo "  1. Create virtual environment: python3 -m venv venv"
    echo "  2. Activate it: source venv/bin/activate  (Linux/Mac)"
    echo "                  venv\\Scripts\\activate     (Windows)"
    echo "  3. Install Python packages: pip install -r requirements.txt"
    exit 0
else
    echo "✗ Some dependencies are missing. Please install them first."
    exit 1
fi
