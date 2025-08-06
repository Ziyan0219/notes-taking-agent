# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered Notes Taking Agent that converts PDF courseware into structured, easy-to-understand notes with practice exercises. The system is built with FastAPI, LangGraph, and OpenAI's API.

## Key Commands

### Development
- **Run the application**: `python app/main.py` or `python start_app.py`
- **Run in development mode**: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- **Run tests**: `python run_tests.py` or `pytest tests/`
- **Code formatting**: `black app/` and `flake8 app/`

### Testing
- Test specific modules: `pytest tests/test_pdf_parser.py -v` or `pytest tests/test_content_analyzer.py -v`
- The `run_tests.py` script provides comprehensive testing including dependency checks and basic import tests

## Architecture

The application follows a modular architecture:

### Core Components
1. **FastAPI Web Interface** (`app/main.py`) - REST API with file upload, processing, and download endpoints
2. **LangGraph Agent Flow** (`app/agents/notes_agent.py`) - Multi-step processing workflow
3. **Agent Manager** (`app/agents/agent_manager.py`) - Coordinates processing jobs and manages state
4. **Processing Services** (`app/services/`) - Specialized services for PDF parsing, content analysis, and note generation

### Key Services
- `pdf_parser.py` - Extracts text, images, and tables from PDFs
- `content_analyzer.py` - Uses AI to identify topics, extract formulas, and analyze document structure
- `enhanced_note_generator.py` - Generates high-quality structured notes
- `note_generator.py` - Fallback note generation service
- `exercise_generator.py` - Creates practice exercises for formulas and concepts

### Data Models
All data structures are defined in `app/models/schemas.py` using Pydantic models:
- `AgentState` - LangGraph workflow state
- `GeneratedNotes` - Complete notes structure with sections and exercises
- `Topic`, `Formula`, `Exercise` - Core content entities
- `ProcessingResult` - Job status and results

## LangGraph Workflow

The PDF processing follows this sequential workflow:
1. `parse_pdf` - Extract content from PDF
2. `analyze_structure` - Identify topics and document structure
3. `extract_formulas` - Find and process mathematical formulas
4. `generate_notes` - Create structured markdown notes
5. `create_exercises` - Generate practice exercises for each formula
6. `create_comprehensive_exercises` - Create complex exercises combining multiple concepts
7. `finalize_notes` - Add exercises to sections and generate summary

## Configuration

### Environment Variables (.env file required)
- `OPENAI_API_KEY` - Required for AI processing
- `APP_HOST` - Default: 0.0.0.0
- `APP_PORT` - Default: 8000
- `DEBUG` - Default: True
- `MAX_FILE_SIZE` - Default: 50MB
- `UPLOAD_DIR` - Default: ./uploads

### File Structure
- `uploads/` - PDF file uploads
- `generated_notes/` - JSON files containing processed notes
- `static/` - Static web assets
- `templates/` - HTML templates for web interface
- `logs/` - Application logs (auto-created)

## Error Handling and Fallbacks

The system implements multiple fallback strategies:
1. **Enhanced Note Generation** → **Basic Note Generation** → **Emergency Fallback**
2. **PDF Conversion**: Uses `manus-md-to-pdf` with WeasyPrint fallback for PDF generation
3. **Formula Extraction**: Graceful degradation when no formulas are found
4. **Exercise Generation**: Creates basic exercises if AI generation fails

## API Endpoints

- `GET /` - Web interface
- `POST /upload` - Upload PDF files
- `POST /process` - Start processing (returns job_id)
- `GET /status/{job_id}` - Check processing status
- `GET /download/{job_id}` - Download generated notes as PDF
- `GET /notes/{notes_id}` - Get raw notes data
- `GET /health` - System health check
- `DELETE /cleanup` - Clean old jobs and temp files

## Testing Notes

- Tests are located in `tests/` directory
- Main test files: `test_pdf_parser.py`, `test_content_analyzer.py`
- Use `run_tests.py` for comprehensive testing including dependency checks
- Mock OpenAI API calls when writing tests to avoid API costs

## Development Tips

- The application uses cost-optimization strategies including intelligent chunking and context reuse
- LaTeX formula processing includes cleaning functions to handle KaTeX compatibility
- Background processing uses asyncio for non-blocking operations
- Job status is tracked in memory with file-based notes storage
- Clean up temporary files regularly using the `/cleanup` endpoint