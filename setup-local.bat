@echo off
setlocal enabledelayedexpansion

rem PDP Carousel Optimizer - Local Setup Script (Windows)
rem This script sets up the complete development environment

echo.
echo 🚀 Setting up PDP Carousel Optimizer locally...
echo =================================================

rem Check if we're in the right directory
if not exist "IMPLEMENTATION_PLAN.md" (
    echo ❌ Please run this script from the root directory ^(where IMPLEMENTATION_PLAN.md is located^)
    exit /b 1
)

rem Navigate to the project directory
cd CarouselOptimizer

echo 📁 Current directory: %cd%

rem Check required tools
echo.
echo 🔍 Checking prerequisites...

python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    exit /b 1
)

node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed. Please install Node.js 18 or higher.
    exit /b 1
)

npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm is not installed. Please install npm.
    exit /b 1
)

echo ✅ All prerequisites are installed

rem Backend Setup
echo.
echo 🔧 Setting up Backend...
echo ========================

cd backend

rem Create virtual environment
echo 📦 Creating Python virtual environment...
if exist "venv" (
    echo Virtual environment already exists, using existing one...
) else (
    python -m venv venv
)

rem Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate

rem Install Python dependencies
echo 📚 Installing Python dependencies...
pip install -r requirements.txt

echo ✅ Backend setup complete!

rem Frontend Setup
echo.
echo 🎨 Setting up Frontend...
echo =========================

cd ..\frontend

rem Install Node.js dependencies
echo 📚 Installing Node.js dependencies...
call npm install

echo ✅ Frontend setup complete!

rem Go back to root
cd ..

rem Create environment files
echo.
echo ⚙️ Setting up environment configuration...
echo ===========================================

rem Backend environment
(
echo # Backend Environment Configuration
echo NODE_ENV=development
echo DEBUG=true
echo LOG_LEVEL=INFO
echo.
echo # Server Configuration  
echo HOST=0.0.0.0
echo PORT=8000
echo.
echo # CORS Configuration
echo CORS_ORIGINS=^["http://localhost:3000", "http://127.0.0.1:3000"^]
echo.
echo # Session Configuration
echo SESSION_TIMEOUT_MINUTES=30
echo CLEANUP_INTERVAL_MINUTES=10
echo.
echo # File Upload Configuration
echo MAX_FILE_SIZE_MB=10
echo MAX_FILES_PER_SESSION=20
echo ALLOWED_EXTENSIONS=^[".jpg", ".jpeg", ".png", ".webp"^]
echo.
echo # Processing Configuration
echo ENABLE_AI_PROCESSING=true
echo ENABLE_QUALITY_METRICS=true
echo MOCK_AI_DATA=true
echo.
echo # Redis Configuration ^(Optional^)
echo REDIS_URL=redis://localhost:6379
echo REDIS_ENABLED=false
) > backend\.env

rem Frontend environment
(
echo # Frontend Environment Configuration
echo VITE_API_BASE_URL=http://localhost:8000
echo VITE_NODE_ENV=development
echo VITE_DEBUG=true
) > frontend\.env

echo ✅ Environment files created!

rem Create run scripts
echo.
echo 📝 Creating convenience scripts...
echo =================================

rem Backend run script
(
echo @echo off
echo call venv\Scripts\activate
echo uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
) > backend\run.bat

rem Frontend run script  
(
echo @echo off
echo npm run dev
) > frontend\run.bat

rem Main run script
(
echo @echo off
echo.
echo echo 🚀 Starting PDP Carousel Optimizer in development mode...
echo.
echo echo 🔧 Starting Backend Server ^(Port 8000^)...
echo cd CarouselOptimizer\backend
echo start "Backend Server" cmd /k run.bat
echo.
echo timeout /t 3 >nul
echo.
echo echo 🎨 Starting Frontend Server ^(Port 3000^)...
echo cd ..\frontend  
echo start "Frontend Server" cmd /k run.bat
echo.
echo cd ..
echo.
echo echo.
echo echo ✅ Both servers are starting!
echo echo 📱 Frontend: http://localhost:3000
echo echo 🔧 Backend:  http://localhost:8000
echo echo 📚 API Docs: http://localhost:8000/docs
echo echo.
echo echo Press any key to continue...
echo pause >nul
) > run-dev.bat

echo ✅ Convenience scripts created!

rem Create test script
(
echo @echo off
echo cd CarouselOptimizer\backend
echo call venv\Scripts\activate
echo pytest tests/ -v --tb=short
echo pause
) > test-backend.bat

echo.
echo 🎉 Setup Complete!
echo ==================
echo.
echo 🚀 Quick Start Commands:
echo   • Run both servers:    run-dev.bat
echo   • Test backend:        test-backend.bat  
echo   • Backend only:        cd CarouselOptimizer\backend ^&^& run.bat
echo   • Frontend only:       cd CarouselOptimizer\frontend ^&^& run.bat
echo.
echo 🌐 Access URLs:
echo   • Frontend:            http://localhost:3000
echo   • Backend API:         http://localhost:8000  
echo   • API Documentation:   http://localhost:8000/docs
echo.
echo 📁 Key Files:
echo   • Backend config:      CarouselOptimizer\backend\.env
echo   • Frontend config:     CarouselOptimizer\frontend\.env
echo   • Requirements:        CarouselOptimizer\backend\requirements.txt
echo.
echo 🔧 To modify AI processing settings, edit backend\.env
echo 🎨 To change frontend configuration, edit frontend\.env
echo.
echo Happy coding! 🎉
echo.
pause