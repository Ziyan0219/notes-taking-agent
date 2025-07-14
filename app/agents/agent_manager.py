"""
Agent Manager for coordinating the notes generation process
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from pathlib import Path
import json
from datetime import datetime

from app.agents.notes_agent import NotesAgent
from app.models.schemas import (
    AgentState, ProcessingResult, ProcessingStatus, GeneratedNotes
)
from app.utils.helpers import generate_unique_id, get_timestamp

logger = logging.getLogger(__name__)


class AgentManager:
    """Manager for coordinating PDF processing agents"""
    
    def __init__(self, openai_api_key: str, model: str = "gpt-3.5-turbo"):
        self.openai_api_key = openai_api_key
        self.model = model
        
        # Active processing jobs
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        
        # Completed results cache
        self.results_cache: Dict[str, ProcessingResult] = {}
        
        # Progress callbacks
        self.progress_callbacks: Dict[str, Callable] = {}
    
    async def start_processing(self, file_path: Path, filename: str, 
                             progress_callback: Optional[Callable] = None) -> str:
        """
        Start processing a PDF file
        
        Args:
            file_path: Path to the PDF file
            filename: Original filename
            progress_callback: Optional callback for progress updates
            
        Returns:
            Job ID for tracking
        """
        job_id = generate_unique_id("job")
        
        logger.info(f"Starting processing job {job_id} for file: {filename}")
        
        # Store job info
        self.active_jobs[job_id] = {
            "filename": filename,
            "file_path": str(file_path),
            "start_time": get_timestamp(),
            "status": ProcessingStatus.PENDING,
            "progress": 0,
            "current_step": "initializing"
        }
        
        if progress_callback:
            self.progress_callbacks[job_id] = progress_callback
        
        # Start processing in background
        asyncio.create_task(self._process_pdf_async(job_id, file_path, filename))
        
        return job_id
    
    async def _process_pdf_async(self, job_id: str, file_path: Path, filename: str):
        """Process PDF asynchronously"""
        
        try:
            # Update status
            self._update_job_status(job_id, ProcessingStatus.PROCESSING, 10, "Initializing agent")
            
            # Create agent
            agent = NotesAgent(self.openai_api_key, self.model)
            
            # Set up progress tracking
            progress_steps = {
                "parsing_pdf": 20,
                "analyzing_structure": 40,
                "extracting_formulas": 60,
                "generating_notes": 75,
                "creating_exercises": 85,
                "creating_comprehensive_exercises": 95,
                "finalizing": 100
            }
            
            # Process with progress tracking
            self._update_job_status(job_id, ProcessingStatus.PROCESSING, 15, "Starting PDF processing")
            
            # Custom progress callback for the agent
            def agent_progress_callback(step: str):
                if step in progress_steps:
                    progress = progress_steps[step]
                    self._update_job_status(job_id, ProcessingStatus.PROCESSING, progress, step)
            
            # Process the PDF
            final_state = await agent.process_pdf(file_path, filename)
            
            # Check for errors - handle both dict and object formats
            error_message = None
            if isinstance(final_state, dict):
                error_message = final_state.get('error')
            elif hasattr(final_state, 'error'):
                error_message = final_state.error
            
            if error_message:
                self._handle_processing_error(job_id, error_message)
                return
            
            # Save results
            processing_time = self._calculate_processing_time(job_id)
            
            # Get notes from final_state - handle both dict and object formats
            notes = None
            notes_id = None
            if isinstance(final_state, dict):
                notes = final_state.get('notes')
                if notes:
                    notes_id = notes.get('id') if isinstance(notes, dict) else getattr(notes, 'id', None)
            elif hasattr(final_state, 'notes'):
                notes = final_state.notes
                if notes:
                    notes_id = getattr(notes, 'id', None)
            
            result = ProcessingResult(
                status=ProcessingStatus.COMPLETED,
                filename=filename,
                progress=100,
                message="Processing completed successfully",
                notes_id=notes_id,
                processing_time=processing_time
            )
            
            self.results_cache[job_id] = result
            
            # Update job status
            self._update_job_status(job_id, ProcessingStatus.COMPLETED, 100, "Processing completed")
            
            # Save notes to file
            if notes:
                await self._save_notes_to_file(notes, job_id)
            
            logger.info(f"Processing job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error in processing job {job_id}: {e}")
            self._handle_processing_error(job_id, str(e))
        
        finally:
            # Clean up
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
    
    def get_job_status(self, job_id: str) -> Optional[ProcessingResult]:
        """
        Get the status of a processing job
        
        Args:
            job_id: Job identifier
            
        Returns:
            Processing result or None if job not found
        """
        # Check completed results first
        if job_id in self.results_cache:
            return self.results_cache[job_id]
        
        # Check active jobs
        if job_id in self.active_jobs:
            job_info = self.active_jobs[job_id]
            
            return ProcessingResult(
                status=job_info["status"],
                filename=job_info["filename"],
                progress=job_info["progress"],
                message=f"Currently: {job_info['current_step']}"
            )
        
        return None
    
    def get_notes(self, notes_id: str) -> Optional[GeneratedNotes]:
        """
        Retrieve generated notes by ID
        
        Args:
            notes_id: Notes identifier
            
        Returns:
            Generated notes or None if not found
        """
        # Try to load from file
        notes_file = Path(f"generated_notes/{notes_id}.json")
        
        if notes_file.exists():
            try:
                with open(notes_file, 'r', encoding='utf-8') as f:
                    notes_data = json.load(f)
                    return GeneratedNotes(**notes_data)
            except Exception as e:
                logger.error(f"Error loading notes {notes_id}: {e}")
        
        return None
    
    def list_completed_jobs(self) -> List[ProcessingResult]:
        """
        List all completed processing jobs
        
        Returns:
            List of completed processing results
        """
        return list(self.results_cache.values())
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """
        Clean up old completed jobs
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
        """
        current_time = datetime.now()
        
        jobs_to_remove = []
        
        for job_id, result in self.results_cache.items():
            # Parse creation time from job_id (contains timestamp)
            try:
                timestamp_str = job_id.split('_')[1]  # Extract timestamp part
                job_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                age_hours = (current_time - job_time).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    jobs_to_remove.append(job_id)
                    
            except Exception:
                # If we can't parse the timestamp, keep the job
                continue
        
        # Remove old jobs
        for job_id in jobs_to_remove:
            del self.results_cache[job_id]
            
            # Also remove notes file
            if hasattr(self.results_cache.get(job_id), 'notes_id'):
                notes_file = Path(f"generated_notes/{self.results_cache[job_id].notes_id}.json")
                if notes_file.exists():
                    notes_file.unlink()
        
        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
    
    def _update_job_status(self, job_id: str, status: ProcessingStatus, 
                          progress: int, current_step: str):
        """Update job status and notify callbacks"""
        
        if job_id in self.active_jobs:
            self.active_jobs[job_id].update({
                "status": status,
                "progress": progress,
                "current_step": current_step,
                "last_update": get_timestamp()
            })
            
            # Call progress callback if available
            if job_id in self.progress_callbacks:
                try:
                    self.progress_callbacks[job_id](progress, current_step)
                except Exception as e:
                    logger.warning(f"Progress callback error for job {job_id}: {e}")
    
    def _handle_processing_error(self, job_id: str, error_message: str):
        """Handle processing errors"""
        
        logger.error(f"Processing error for job {job_id}: {error_message}")
        
        result = ProcessingResult(
            status=ProcessingStatus.FAILED,
            filename=self.active_jobs.get(job_id, {}).get("filename", "unknown"),
            progress=0,
            message="Processing failed",
            error=error_message
        )
        
        self.results_cache[job_id] = result
        
        # Update job status
        if job_id in self.active_jobs:
            self.active_jobs[job_id].update({
                "status": ProcessingStatus.FAILED,
                "error": error_message
            })
    
    def _calculate_processing_time(self, job_id: str) -> float:
        """Calculate processing time for a job"""
        
        if job_id not in self.active_jobs:
            return 0.0
        
        start_time_str = self.active_jobs[job_id]["start_time"]
        
        try:
            start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.now()
            
            return (end_time - start_time).total_seconds()
            
        except Exception:
            return 0.0
    
    async def _save_notes_to_file(self, notes: GeneratedNotes, job_id: str):
        """Save generated notes to file"""
        
        try:
            # Ensure directory exists
            notes_dir = Path("generated_notes")
            notes_dir.mkdir(exist_ok=True)
            
            # Save as JSON
            notes_file = notes_dir / f"{notes.id}.json"
            
            # Convert to dict for JSON serialization
            notes_dict = notes.dict()
            
            with open(notes_file, 'w', encoding='utf-8') as f:
                json.dump(notes_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Notes saved to {notes_file}")
            
        except Exception as e:
            logger.error(f"Error saving notes for job {job_id}: {e}")
    
    def export_notes_as_markdown(self, notes_id: str) -> Optional[str]:
        """
        Export notes as Markdown format
        
        Args:
            notes_id: Notes identifier
            
        Returns:
            Markdown content or None if notes not found
        """
        notes = self.get_notes(notes_id)
        
        if not notes:
            return None
        
        markdown_parts = []
        
        # Title
        markdown_parts.append(f"# {notes.title}\n")
        
        # Metadata
        markdown_parts.append(f"**Source**: {notes.source_filename}")
        markdown_parts.append(f"**Created**: {notes.created_at}")
        markdown_parts.append(f"**Summary**: {notes.summary}\n")
        
        # Sections
        for section in notes.sections:
            markdown_parts.append(section.content)
            
            # Add exercises
            if section.exercises:
                markdown_parts.append("### Practice Exercises\n")
                
                for idx, exercise in enumerate(section.exercises, 1):
                    markdown_parts.append(f"**Exercise {idx}** (Difficulty: {exercise.difficulty}/5)")
                    markdown_parts.append(f"{exercise.question}\n")
                    
                    if exercise.solution:
                        markdown_parts.append(f"*Solution approach*: {exercise.solution}\n")
        
        # Comprehensive exercises
        if notes.comprehensive_exercises:
            markdown_parts.append("## Comprehensive Exercises\n")
            
            for idx, exercise in enumerate(notes.comprehensive_exercises, 1):
                markdown_parts.append(f"### Comprehensive Exercise {idx}")
                markdown_parts.append(f"**Difficulty**: {exercise.difficulty}/5\n")
                markdown_parts.append(f"{exercise.question}\n")
                
                if exercise.solution:
                    markdown_parts.append(f"**Solution Approach**:")
                    markdown_parts.append(f"{exercise.solution}\n")
        
        return "\n".join(markdown_parts)
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics
        
        Returns:
            Dictionary with processing statistics
        """
        total_jobs = len(self.results_cache)
        successful_jobs = len([r for r in self.results_cache.values() 
                              if r.status == ProcessingStatus.COMPLETED])
        failed_jobs = len([r for r in self.results_cache.values() 
                          if r.status == ProcessingStatus.FAILED])
        active_jobs = len(self.active_jobs)
        
        avg_processing_time = 0.0
        if successful_jobs > 0:
            processing_times = [r.processing_time for r in self.results_cache.values() 
                              if r.processing_time and r.status == ProcessingStatus.COMPLETED]
            if processing_times:
                avg_processing_time = sum(processing_times) / len(processing_times)
        
        return {
            "total_jobs": total_jobs,
            "successful_jobs": successful_jobs,
            "failed_jobs": failed_jobs,
            "active_jobs": active_jobs,
            "success_rate": (successful_jobs / total_jobs * 100) if total_jobs > 0 else 0,
            "average_processing_time": avg_processing_time
        }

