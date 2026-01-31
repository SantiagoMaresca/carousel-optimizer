#!/bin/bash

# PDP Carousel Optimizer - Local Setup Script
# This script sets up the complete development environment

set -e  # Exit on any error

echo "🚀 Setting up PDP Carousel Optimizer locally..."
echo "================================================="

# Check if we're in the right directory
if [ ! -f "IMPLEMENTATION_PLAN.md" ]; then
    echo "❌ Please run this script from the root directory (where IMPLEMENTATION_PLAN.md is located)"
    exit 1
fi

# Navigate to the project directory
cd CarouselOptimizer

echo "📁 Current directory: $(pwd)"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required tools
echo "🔍 Checking prerequisites..."

if ! command_exists python3; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm is not installed. Please install npm."
    exit 1
fi

echo "✅ All prerequisites are installed"

# Backend Setup
echo ""
echo "🔧 Setting up Backend..."
echo "========================"

cd backend

# Create virtual environment
echo "📦 Creating Python virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists, using existing one..."
else
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Backend setup complete!"

# Frontend Setup
echo ""
echo "🎨 Setting up Frontend..."
echo "========================="

cd ../frontend

# Install Node.js dependencies
echo "📚 Installing Node.js dependencies..."
npm install

echo "✅ Frontend setup complete!"

# Go back to root
cd ..

# Create environment files
echo ""
echo "⚙️  Setting up environment configuration..."
echo "==========================================="

# Backend environment
cat > backend/.env << EOF
# Backend Environment Configuration
NODE_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# Server Configuration  
HOST=0.0.0.0
PORT=8000

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# Session Configuration
SESSION_TIMEOUT_MINUTES=30
CLEANUP_INTERVAL_MINUTES=10

# File Upload Configuration
MAX_FILE_SIZE_MB=10
MAX_FILES_PER_SESSION=20
ALLOWED_EXTENSIONS=[".jpg", ".jpeg", ".png", ".webp"]

# Processing Configuration
ENABLE_AI_PROCESSING=true
ENABLE_QUALITY_METRICS=true
MOCK_AI_DATA=true

# Redis Configuration (Optional)
REDIS_URL=redis://localhost:6379
REDIS_ENABLED=false
EOF

# Frontend environment
cat > frontend/.env << EOF
# Frontend Environment Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_NODE_ENV=development
VITE_DEBUG=true
EOF

echo "✅ Environment files created!"

# Create run scripts
echo ""
echo "📝 Creating convenience scripts..."
echo "================================="

# Backend run script
cat > backend/run.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
EOF

# Frontend run script  
cat > frontend/run.sh << 'EOF'
#!/bin/bash
npm run dev
EOF

# Make scripts executable
chmod +x backend/run.sh
chmod +x frontend/run.sh

# Main run script
cat > run-dev.sh << 'EOF'
#!/bin/bash

# PDP Carousel Optimizer - Development Server Runner
echo "🚀 Starting PDP Carousel Optimizer in development mode..."

# Function to kill background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

# Set up signal handlers
trap cleanup INT TERM

# Start backend
echo "🔧 Starting Backend Server (Port 8000)..."
cd CarouselOptimizer/backend
./run.sh &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "🎨 Starting Frontend Server (Port 3000)..."
cd ../frontend
./run.sh &
FRONTEND_PID=$!

echo ""
echo "✅ Both servers are running!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend:  http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
EOF

chmod +x run-dev.sh

echo "✅ Convenience scripts created!"

# Create test script
cat > test-backend.sh << 'EOF'
#!/bin/bash
cd CarouselOptimizer/backend
source venv/bin/activate
pytest tests/ -v --tb=short
EOF

chmod +x test-backend.sh

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "🚀 Quick Start Commands:"
echo "  • Run both servers:    ./run-dev.sh"
echo "  • Test backend:        ./test-backend.sh"  
echo "  • Backend only:        cd CarouselOptimizer/backend && ./run.sh"
echo "  • Frontend only:       cd CarouselOptimizer/frontend && ./run.sh"
echo ""
echo "🌐 Access URLs:"
echo "  • Frontend:            http://localhost:3000"
echo "  • Backend API:         http://localhost:8000"  
echo "  • API Documentation:   http://localhost:8000/docs"
echo ""
echo "📁 Key Files:"
echo "  • Backend config:      CarouselOptimizer/backend/.env"
echo "  • Frontend config:     CarouselOptimizer/frontend/.env"
echo "  • Requirements:        CarouselOptimizer/backend/requirements.txt"
echo ""
echo "🔧 To modify AI processing settings, edit backend/.env"
echo "🎨 To change frontend configuration, edit frontend/.env"
echo ""
echo "Happy coding! 🎉"