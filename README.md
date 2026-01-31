# Carousel Optimizer 🎠🤖

> **AI-Powered Image Analysis** using OpenAI's CLIP model for intelligent carousel optimization with automated quality metrics, visual similarity detection, and smart ordering recommendations.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org)
[![AI](https://img.shields.io/badge/AI-CLIP%20Model-orange.svg)](https://github.com/openai/CLIP)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🧠 AI Technology

This application leverages cutting-edge **Computer Vision AI** to analyze and optimize image carousels:

### **OpenAI CLIP Model** 
- **What it is**: Contrastive Language-Image Pre-Training - a neural network trained on 400M image-text pairs
- **What we use it for**: Generates 512-dimensional embeddings that capture semantic image content
- **Why it matters**: Understands image similarity beyond pixel comparison - recognizes objects, scenes, and concepts
- **Implementation**: `open-clip-torch` library with ViT-B-32 architecture (151M parameters)

### **AI-Powered Features**

#### 1. **Visual Similarity Detection** 🔍
- Compares CLIP embeddings using cosine similarity
- Detects duplicate images (>95% similarity)
- Identifies related images (>80% similarity)
- Groups similar content for better carousel flow

#### 2. **Computer Vision Quality Metrics** 📊
Using OpenCV and custom algorithms:
- **Blur Detection**: Laplacian variance analysis to identify out-of-focus images
- **Brightness Analysis**: Histogram analysis for optimal exposure
- **Contrast Evaluation**: Standard deviation of pixel values
- **Resolution Check**: Ensures images meet minimum quality standards

#### 3. **Smart Ordering Algorithm** 🎯
- Prioritizes high-quality images first
- Removes duplicates automatically
- Groups similar images for narrative flow
- Maximizes user engagement potential

## 🌟 Features

### **Production Stack**
- **Backend**: FastAPI + PyTorch + OpenAI CLIP model
- **Frontend**: React 18 + Vite + Tailwind CSS
- **Storage**: Cloudflare R2 (S3-compatible)
- **Deployment**: Render.com + Vercel
- **AI/ML**: OpenCV, scikit-learn, NumPy

### User Experience
- **Drag & Drop Upload**: Modern file upload with progress tracking
- **Real-time Processing**: Instant analysis with live progress updates
- **Interactive Results**: Comprehensive dashboard with multiple view modes
- **Export Capabilities**: JSON export of analysis results

### Technical Excellence
- **Scalable Architecture**: Modular FastAPI backend with session management
- **Modern Frontend**: React 18 with Zustand state management and Tailwind CSS
- **Comprehensive Testing**: 94% test coverage with pytest framework
- **Production Ready**: Docker support, logging, and deployment configuration

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **Git** for version control

### One-Command Setup

#### Windows
```powershell
# Clone the repository
git clone <your-repo-url>
cd carousel-optimizer

# Run setup script
setup-local.bat
```

#### Linux/macOS
```bash
# Clone the repository
git clone <your-repo-url>
cd carousel-optimizer

# Make script executable and run
chmod +x setup-local.sh
./setup-local.sh
```

### Manual Setup

<details>
<summary>Click to expand manual setup instructions</summary>

#### Backend Setup
```bash
cd CarouselOptimizer/backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/macOS  
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd CarouselOptimizer/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

</details>

## 📁 Project Structure

```
CarouselOptimizer/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── main.py            # FastAPI application entry point
│   │   ├── routers/           # API route definitions
│   │   └── core/              # Core business logic
│   ├── modules/               # AI processing modules
│   │   ├── embeddings.py      # CLIP embeddings for similarity
│   │   └── quality_metrics.py # Image quality analysis
│   ├── tests/                 # Comprehensive test suite
│   └── requirements.txt       # Python dependencies
│
├── frontend/                  # React Frontend
│   ├── src/
│   │   ├── components/        # Reusable React components
│   │   ├── pages/            # Main application pages
│   │   ├── services/         # API integration layer
│   │   └── stores/           # Zustand state management
│   └── package.json          # Node.js dependencies
│
├── docs/                     # Documentation
├── deployment/               # Deployment configurations
└── setup-local.*            # Local setup scripts
```

## 🛠️ Development

### Running in Development Mode

#### All Services
```bash
# Windows
run-dev.bat

# Linux/macOS
./run-dev.sh
```

#### Individual Services
```bash
# Backend only
cd CarouselOptimizer/backend && ./run.sh

# Frontend only  
cd CarouselOptimizer/frontend && ./run.sh
```

### Testing

#### Backend Tests
```bash
# Run all tests
./test-backend.sh

# Or manually
cd CarouselOptimizer/backend
source venv/bin/activate  # Windows: venv\Scripts\activate
pytest tests/ -v
```

#### Frontend Tests
```bash
cd CarouselOptimizer/frontend
npm test
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React application |
| Backend API | http://localhost:8000 | FastAPI server |
| API Documentation | http://localhost:8000/docs | Interactive API docs |
| Alternative Docs | http://localhost:8000/redoc | ReDoc API docs |

## 🔧 Configuration

### Environment Variables

#### Backend Configuration (`backend/.env`)
```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
NODE_ENV=development

# Processing Configuration
ENABLE_AI_PROCESSING=true
ENABLE_QUALITY_METRICS=true
MOCK_AI_DATA=true

# File Upload Limits
MAX_FILE_SIZE_MB=10
MAX_FILES_PER_SESSION=20
ALLOWED_EXTENSIONS=[".jpg", ".jpeg", ".png", ".webp"]

# Session Management
SESSION_TIMEOUT_MINUTES=30
CLEANUP_INTERVAL_MINUTES=10
```

#### Frontend Configuration (`frontend/.env`)
```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_NODE_ENV=development
VITE_DEBUG=true
```

## 📚 API Documentation

### Core Endpoints

#### Upload Images
```http
POST /sessions/{session_id}/upload
Content-Type: multipart/form-data

# Upload multiple images for analysis
```

#### Start Analysis  
```http
POST /sessions/{session_id}/analyze
Content-Type: application/json

{
  "enable_ai": true,
  "enable_quality": true
}
```

#### Get Results
```http
GET /sessions/{session_id}/results

# Returns complete analysis with recommendations
```

### Response Format
```json
{
  "session_id": "uuid",
  "processing_time_ms": 1500,
  "images": [
    {
      "id": "img_001",
      "filename": "product1.jpg",
      "quality_metrics": {
        "composite_score": 85.2,
        "blur_score": 92.1,
        "brightness": 128.5,
        "contrast": 45.8,
        "resolution": [1920, 1080],
        "flags": [],
        "suggestions": ["Increase brightness slightly"]
      }
    }
  ],
  "recommended_order": [
    {
      "image_id": "img_001",
      "position": 1,
      "score": 95.5,
      "is_hero": true,
      "reason": "Highest quality score with optimal composition"
    }
  ],
  "duplicates": [],
  "hero_image": "img_001"
}
```

## 🐳 Docker Deployment

### Build Images
```bash
# Backend
cd CarouselOptimizer/backend
docker build -t carousel-optimizer-backend .

# Frontend  
cd ../frontend
docker build -t carousel-optimizer-frontend .
```

### Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## ☁️ Cloud Deployment

### Railway Deployment

<details>
<summary>Deploy to Railway</summary>

1. **Connect Repository**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login and link project
   railway login
   railway link
   ```

2. **Deploy Backend**
   ```bash
   cd CarouselOptimizer/backend
   railway up
   ```

3. **Deploy Frontend**
   ```bash
   cd ../frontend
   railway up
   ```

4. **Configure Environment**
   - Set `VITE_API_BASE_URL` to your backend Railway URL
   - Configure domain settings in Railway dashboard

</details>

### Render Deployment

<details>
<summary>Deploy to Render</summary>

1. **Backend Service**
   - Connect repository on Render
   - Set build command: `cd CarouselOptimizer/backend && pip install -r requirements.txt`
   - Set start command: `cd CarouselOptimizer/backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

2. **Frontend Service**  
   - Create static site service
   - Set build command: `cd CarouselOptimizer/frontend && npm install && npm run build`
   - Set publish directory: `CarouselOptimizer/frontend/dist`
   - Configure `VITE_API_BASE_URL` environment variable

</details>

### AWS Deployment

<details>
<summary>Deploy to AWS</summary>

#### Using AWS App Runner

1. **Create apprunner.yaml**
   ```yaml
   version: 1.0
   runtime: python3
   build:
     commands:
       build:
         - cd CarouselOptimizer/backend
         - pip install -r requirements.txt
   run:
     runtime-version: 3.9
     command: uvicorn app.main:app --host 0.0.0.0 --port 8000
     network:
       port: 8000
   ```

2. **Deploy via Console**
   - Create App Runner service
   - Connect to GitHub repository
   - Configure auto-deployment

#### Using Elastic Beanstalk

1. **Initialize EB CLI**
   ```bash
   cd CarouselOptimizer/backend
   eb init carousel-optimizer-api
   eb create production
   ```

2. **Frontend to S3 + CloudFront**
   ```bash
   cd ../frontend
   npm run build
   aws s3 sync dist/ s3://your-bucket-name
   ```

</details>

## 🔍 Monitoring & Debugging

### Logging

The application uses structured logging throughout:

```python
# Backend logging
import logging
logger = logging.getLogger(__name__)

logger.info("Processing started", extra={"session_id": session_id})
logger.error("Processing failed", extra={"error": str(e), "session_id": session_id})
```

### Health Checks

```http
GET /health
# Returns system status and dependencies

GET /sessions/{session_id}/status  
# Returns session processing status
```

### Performance Monitoring

- **Response Times**: Tracked in all API endpoints
- **Memory Usage**: Monitored during image processing
- **Session Metrics**: Active sessions and cleanup stats
- **Error Rates**: Comprehensive error tracking and alerts

## 🧪 Testing Strategy

### Backend Testing (94% Coverage)

- **Unit Tests**: Core business logic validation
- **Integration Tests**: API endpoint testing  
- **Performance Tests**: Load testing for image processing
- **Mock Tests**: AI component testing without dependencies

### Frontend Testing

- **Component Tests**: React component behavior
- **Integration Tests**: API integration validation
- **E2E Tests**: Complete user workflow testing

### Test Commands

```bash
# Run all tests with coverage
cd CarouselOptimizer/backend
pytest tests/ --cov=app --cov-report=html

# Run specific test category
pytest tests/test_api.py -v
pytest tests/test_quality.py -v
pytest tests/test_sessions.py -v
```

## 🚨 Troubleshooting

<details>
<summary>Common Issues and Solutions</summary>

### Backend Issues

**Issue: Import errors for OpenCV/CLIP**
```bash
# Solution: Check if running in mock mode
export MOCK_AI_DATA=true
# Or install full dependencies
pip install opencv-python open-clip-torch
```

**Issue: Port already in use**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9
# Or use different port
uvicorn app.main:app --port 8001
```

### Frontend Issues  

**Issue: API connection failed**
- Check `VITE_API_BASE_URL` in `frontend/.env`
- Verify backend is running on correct port
- Check CORS configuration in backend

**Issue: Build failures**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Deployment Issues

**Issue: Environment variables not loading**
- Verify `.env` files are not in `.gitignore`
- Check environment variable syntax
- Restart services after changes

</details>

## 🤝 Contributing

### Development Workflow

1. **Fork and Clone**
   ```bash
   git fork <repo-url>
   git clone <your-fork-url>
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Setup Development Environment**
   ```bash
   ./setup-local.sh  # or setup-local.bat
   ```

4. **Make Changes and Test**
   ```bash
   # Test backend
   ./test-backend.sh
   
   # Test frontend  
   cd CarouselOptimizer/frontend && npm test
   ```

5. **Submit Pull Request**
   - Ensure tests pass
   - Update documentation
   - Add descriptive commit messages

### Code Style

- **Python**: Black formatting, flake8 linting
- **JavaScript**: ESLint with React plugins
- **Commits**: Conventional commit format

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

### Documentation
- 📚 [API Documentation](http://localhost:8000/docs)
- 🎥 [Video Tutorials](docs/tutorials/)
- 📖 [Architecture Guide](docs/architecture.md)

### Community
- 💬 [Discord Server](https://discord.gg/your-server)
- 📋 [GitHub Issues](../../issues)
- 🐛 [Bug Reports](../../issues/new?template=bug_report.md)
- 💡 [Feature Requests](../../issues/new?template=feature_request.md)

## 🎯 Roadmap

### Current Version (v1.0)
- ✅ Core image analysis
- ✅ Quality metrics
- ✅ Similarity detection
- ✅ React frontend
- ✅ API documentation

### Next Release (v1.1)
- 🔄 Batch processing improvements
- 🔄 Advanced ML models
- 🔄 Performance optimizations
- 🔄 Mobile-responsive UI

### Future Releases
- 📋 A/B testing framework
- 📋 Real-time collaboration
- 📋 Advanced analytics dashboard
- 📋 Third-party integrations

---

<div align="center">

**Built with ❤️ for e-commerce optimization**

[⭐ Star this repo](../../stargazers) • [🐛 Report Bug](../../issues) • [💡 Request Feature](../../issues)

</div>