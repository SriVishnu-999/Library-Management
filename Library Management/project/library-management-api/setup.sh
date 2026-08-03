#!/usr/bin/env bash
#
# Setup script — installs dependencies and optionally seeds the database.
#
set -e

echo "=========================================="
echo "  Library Management REST API — Setup"
echo "=========================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed. Please install Python 3.8+."
    exit 1
fi

echo "Python version: $(python3 --version)"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv
echo "Virtual environment created at ./venv"

# Activate and install
echo ""
echo "Installing dependencies..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

pip install --upgrade pip -q
pip install -r requirements.txt -q

echo ""
echo "Dependencies installed successfully."
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "WARNING: No .env file found."
    echo "Please copy .env.example to .env and configure your DATABASE_URL:"
    echo "  cp .env.example .env"
    echo "  # Then edit .env with your PostgreSQL connection string"
    echo ""
else
    echo ".env file found."
fi

echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "To start the API:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate  (Linux/Mac)"
echo "     venv\\Scripts\\activate     (Windows)"
echo "  2. Configure DATABASE_URL in .env"
echo "  3. Run: python seed.py   (optional — loads sample data)"
echo "  4. Run: python run.py"
echo ""
echo "The API will be available at: http://localhost:5000"
echo ""
echo "Import the Postman collection from the postman/ folder to test all endpoints."
