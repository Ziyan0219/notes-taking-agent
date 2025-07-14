"""
FastAPI main application for Notes Taking Agent
"""

import os
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import logging

from app.agents.agent_manager import AgentManager
from app.services.note_generator import NoteGenerator
from app.models.schemas import ProcessRequest, StatusResponse, UploadResponse
from app.utils.helpers import clean_filename, format_file_size, ensure_directory_exists

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Notes Taking Agent",
    description="AI-powered PDF to structured notes converter",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Configuration
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
ensure_directory_exists(Path("generated_notes"))

# Initialize services
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY not found in environment variables")
    raise ValueError("OPENAI_API_KEY is required")

agent_manager = AgentManager(OPENAI_API_KEY)
note_generator = NoteGenerator()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload PDF file for processing"""
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Read and validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File size too large. Maximum size: {format_file_size(MAX_FILE_SIZE)}")
    
    # Clean filename
    clean_name = clean_filename(file.filename)
    file_path = UPLOAD_DIR / clean_name
    
    # Handle duplicate filenames
    counter = 1
    original_path = file_path
    while file_path.exists():
        stem = original_path.stem
        suffix = original_path.suffix
        file_path = original_path.parent / f"{stem}_{counter}{suffix}"
        counter += 1
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"File uploaded: {file_path}")
        
        return UploadResponse(
            message="File uploaded successfully",
            filename=file_path.name,
            file_path=str(file_path),
            file_size=len(content)
        )
        
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")


@app.post("/process")
async def process_pdf(request: ProcessRequest, background_tasks: BackgroundTasks):
    """Start PDF processing"""
    
    file_path = UPLOAD_DIR / request.filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Start processing in background
        job_id = await agent_manager.start_processing(file_path, request.filename)
        
        logger.info(f"Started processing job {job_id} for file: {request.filename}")
        
        return JSONResponse({
            "message": "PDF processing started",
            "job_id": job_id,
            "status": "processing",
            "filename": request.filename
        })
        
    except Exception as e:
        logger.error(f"Error starting processing: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/status/{job_id}", response_model=StatusResponse)
async def get_processing_status(job_id: str):
    """Get processing status for a job"""
    
    result = agent_manager.get_job_status(job_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return StatusResponse(
        filename=result.filename,
        status=result.status,
        progress=result.progress,
        message=result.message,
        estimated_time=None  # Could be calculated based on progress
    )


@app.get("/download/{job_id}")
async def download_notes(job_id: str, format: str = "pdf"):
    """Download generated notes as PDF"""
    
    result = agent_manager.get_job_status(job_id)
    
    if not result or not result.notes_id:
        raise HTTPException(status_code=404, detail="Notes not found")
    
    notes = agent_manager.get_notes(result.notes_id)
    
    if not notes:
        raise HTTPException(status_code=404, detail="Notes not available")
    
    try:
        # Export as Markdown first
        markdown_content = note_generator.export_to_markdown(notes)
        
        # Create temporary markdown file
        temp_md_file = Path(f"temp_notes_{job_id}.md")
        with open(temp_md_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        if format.lower() == "pdf":
            # Convert markdown to PDF using manus utility
            temp_pdf_file = Path(f"temp_notes_{job_id}.pdf")
            
            # Use manus-md-to-pdf utility
            import subprocess
            result = subprocess.run([
                "manus-md-to-pdf", 
                str(temp_md_file), 
                str(temp_pdf_file)
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"PDF conversion failed: {result.stderr}")
                raise HTTPException(status_code=500, detail="PDF conversion failed")
            
            # Clean up markdown file
            temp_md_file.unlink(missing_ok=True)
            
            return FileResponse(
                path=temp_pdf_file,
                filename=f"{notes.title.replace(' ', '_')}.pdf",
                media_type="application/pdf"
            )
            
        elif format.lower() == "markdown":
            # Return markdown file
            return FileResponse(
                path=temp_md_file,
                filename=f"{notes.title.replace(' ', '_')}.md",
                media_type="text/markdown"
            )
            
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'pdf' or 'markdown'")
            
    except Exception as e:
        logger.error(f"Error generating download: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate download")


@app.get("/notes/{notes_id}")
async def get_notes(notes_id: str):
    """Get notes by ID"""
    
    notes = agent_manager.get_notes(notes_id)
    
    if not notes:
        raise HTTPException(status_code=404, detail="Notes not found")
    
    return notes


@app.get("/notes/{notes_id}/preview")
async def preview_notes(notes_id: str, request: Request):
    """Preview notes in HTML format"""
    
    notes = agent_manager.get_notes(notes_id)
    
    if not notes:
        raise HTTPException(status_code=404, detail="Notes not found")
    
    # Convert to markdown and then to HTML for preview
    markdown_content = note_generator.export_to_markdown(notes)
    
    return templates.TemplateResponse("notes_preview.html", {
        "request": request,
        "notes": notes,
        "markdown_content": markdown_content
    })


@app.get("/jobs")
async def list_jobs():
    """List all completed jobs"""
    
    jobs = agent_manager.list_completed_jobs()
    
    return {
        "jobs": jobs,
        "total": len(jobs)
    }


@app.get("/statistics")
async def get_statistics():
    """Get processing statistics"""
    
    stats = agent_manager.get_processing_statistics()
    
    return stats


@app.delete("/cleanup")
async def cleanup_old_jobs(max_age_hours: int = 24):
    """Clean up old jobs and files"""
    
    try:
        agent_manager.cleanup_old_jobs(max_age_hours)
        
        # Clean up temporary files
        temp_files = Path(".").glob("temp_notes_*.md")
        temp_files_json = Path(".").glob("temp_notes_*.json")
        
        cleaned_files = 0
        for temp_file in list(temp_files) + list(temp_files_json):
            try:
                temp_file.unlink()
                cleaned_files += 1
            except:
                pass
        
        return {
            "message": "Cleanup completed",
            "cleaned_temp_files": cleaned_files
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail="Cleanup failed")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    
    # Check if OpenAI API key is available
    api_key_status = "configured" if OPENAI_API_KEY else "missing"
    
    # Check upload directory
    upload_dir_status = "accessible" if UPLOAD_DIR.exists() else "missing"
    
    return {
        "status": "healthy",
        "service": "Notes Taking Agent",
        "version": "1.0.0",
        "api_key": api_key_status,
        "upload_directory": upload_dir_status,
        "active_jobs": len(agent_manager.active_jobs),
        "completed_jobs": len(agent_manager.results_cache)
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug
    )

