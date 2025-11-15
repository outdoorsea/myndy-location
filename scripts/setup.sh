#!/bin/bash
# Setup Script for Location Intelligence Service
# File: scripts/setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 Setting up Location Intelligence Service..."
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed. Aborting." >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Aborting." >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed. Aborting." >&2; exit 1; }
echo "✅ Prerequisites checked"
echo ""

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
cd "$PROJECT_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ .env created (please update with your settings)"
else
    echo "✅ .env already exists"
fi
echo ""

# Initialize database
echo "🗄️  Initializing database..."
if docker ps --format '{{.Names}}' | grep -q "location-postgres"; then
    echo "✅ Database container is running"

    # Run migrations
    echo "🔄 Running database migrations..."
    alembic upgrade head
    echo "✅ Migrations completed"
else
    echo "⚠️  Database container not running. Start it with:"
    echo "   docker-compose -f ../docker-compose.unified.yml up -d location-postgres"
fi
echo ""

# Summary
echo "✅ Setup complete!"
echo ""
echo "📚 Next steps:"
echo "   1. Update .env with your database credentials"
echo "   2. Start the database: docker-compose -f ../docker-compose.unified.yml up -d location-postgres"
echo "   3. Run migrations: alembic upgrade head"
echo "   4. Start the service: uvicorn api.main:app --reload --port 8003"
echo "   5. Visit: http://localhost:8004/docs"
echo ""
