"""
Simple FastAPI application for local development
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uuid
import os
import logging
from pathlib import Path

# Configure simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("carousel_optimizer")

# Create FastAPI app
app = FastAPI(
    title="Carousel Optimizer API",
    description="AI-powered image carousel optimization",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory storage
sessions = {}
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.get("/")
async def root():
    """Root endpoint"""
    logger.info("Root endpoint accessed")
    return {"message": "Carousel Optimizer API is running!"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "version": "1.0.0",
        "message": "All systems operational"
    }

@app.post("/sessions")
async def create_session():
    """Create a new session"""
    session_id = str(uuid.uuid4())
    logger.info(f"Creating new session: {session_id}")
    sessions[session_id] = {
        "id": session_id,
        "images": [],
        "status": "created"
    }
    logger.info(f"Session {session_id} created successfully")
    return {"session_id": session_id}

@app.post("/sessions/{session_id}/upload")
async def upload_images(session_id: str, files: List[UploadFile] = File(...)):
    """Upload images to a session"""
    logger.info(f"File upload requested for session: {session_id}, files count: {len(files)}")
    
    if session_id not in sessions:
        logger.warning(f"Upload attempted for non-existent session: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")
    
    uploaded_files = []
    for file in files:
        logger.info(f"Processing file: {file.filename}, size: {file.size if hasattr(file, 'size') else 'unknown'}")
        # Save file
        file_path = UPLOAD_DIR / f"{session_id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        uploaded_files.append({
            "filename": file.filename,
            "size": len(content),
            "path": str(file_path)
        })
    
    sessions[session_id]["images"] = uploaded_files
    sessions[session_id]["status"] = "uploaded"
    
    logger.info(f"Successfully uploaded {len(uploaded_files)} files for session {session_id}")
    
    return {
        "session_id": session_id,
        "uploaded_files": len(uploaded_files),
        "files": uploaded_files
    }

@app.post("/sessions/{session_id}/analyze")
async def analyze_images(session_id: str):
    """Analyze images (mock implementation)"""
    logger.info(f"Analysis requested for session: {session_id}")
    
    if session_id not in sessions:
        logger.warning(f"Analysis attempted for non-existent session: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    images = session["images"]
    logger.info(f"Analyzing {len(images)} images for session {session_id}")
    
    # Mock analysis results
    results = {
        "session_id": session_id,
        "processing_time_ms": 1250,
        "images": [],
        "recommended_order": [],
        "duplicates": [],
        "hero_image": None
    }
    
    # Generate mock data for each image
    for i, image in enumerate(images):
        image_data = {
            "id": f"img_{i+1:03d}",
            "filename": image["filename"],
            "quality_metrics": {
                "composite_score": 85.0 + (i * 2),
                "blur_score": 90.0 + (i * 1.5),
                "brightness": 120.0 + (i * 3),
                "contrast": 45.0 + (i * 2),
                "resolution": [1920, 1080],
                "flags": [],
                "suggestions": ["Great quality!" if i == 0 else "Consider improving lighting"]
            }
        }
        results["images"].append(image_data)
        
        # Add to recommended order
        results["recommended_order"].append({
            "image_id": f"img_{i+1:03d}",
            "position": i + 1,
            "score": 95.0 - (i * 2),
            "is_hero": i == 0,
            "reason": "Highest quality score" if i == 0 else "Good secondary image"
        })
    
    if images:
        results["hero_image"] = "img_001"
    
    sessions[session_id]["results"] = results
    sessions[session_id]["status"] = "analyzed"
    
    logger.info(f"Analysis completed for session {session_id}: {len(results['images'])} images processed")
    
    return results

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    logger.info(f"Session info requested for: {session_id}")
    
    if session_id not in sessions:
        logger.warning(f"Attempted to access non-existent session: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")
    
    return sessions[session_id]

@app.get("/sessions/{session_id}/results")
async def get_results(session_id: str):
    """Get analysis results"""
    logger.info(f"Results requested for session: {session_id}")
    
    if session_id not in sessions:
        logger.warning(f"Results requested for non-existent session: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    if "results" not in session:
        logger.warning(f"Results requested for session {session_id} but analysis not completed")
        raise HTTPException(status_code=400, detail="Analysis not completed yet")
    
    logger.info(f"Returning results for session {session_id}")
    return session["results"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)