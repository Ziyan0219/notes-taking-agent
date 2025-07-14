"""
Data models and schemas for the Notes Taking Agent
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ProcessingStatus(str, Enum):
    """Processing status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TopicType(str, Enum):
    """Topic type enumeration"""
    CHAPTER = "chapter"
    SECTION = "section"
    SUBSECTION = "subsection"
    CONCEPT = "concept"


class FormulaType(str, Enum):
    """Formula type enumeration"""
    EQUATION = "equation"
    THEOREM = "theorem"
    DEFINITION = "definition"
    PROPERTY = "property"


class ExerciseType(str, Enum):
    """Exercise type enumeration"""
    SIMPLE_APPLICATION = "simple_application"
    COMPREHENSIVE = "comprehensive"
    DERIVATION = "derivation"
    CONCEPTUAL = "conceptual"


class PDFContent(BaseModel):
    """Raw PDF content structure"""
    text: str = Field(..., description="Extracted text content")
    pages: int = Field(..., description="Number of pages")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="PDF metadata")
    images: List[str] = Field(default_factory=list, description="Extracted image paths")
    tables: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted tables")


class Topic(BaseModel):
    """Topic structure"""
    id: str = Field(..., description="Unique topic identifier")
    title: str = Field(..., description="Topic title")
    type: TopicType = Field(..., description="Topic type")
    level: int = Field(..., description="Hierarchical level (1=chapter, 2=section, etc.)")
    parent_id: Optional[str] = Field(None, description="Parent topic ID")
    content: str = Field(..., description="Topic content")
    page_range: tuple[int, int] = Field(..., description="Start and end page numbers")
    keywords: List[str] = Field(default_factory=list, description="Key terms and concepts")


class Formula(BaseModel):
    """Formula structure"""
    id: str = Field(..., description="Unique formula identifier")
    name: str = Field(..., description="Formula name or description")
    latex: str = Field(..., description="LaTeX representation")
    type: FormulaType = Field(..., description="Formula type")
    topic_id: str = Field(..., description="Associated topic ID")
    derivation: Optional[str] = Field(None, description="Derivation explanation")
    source: Optional[str] = Field(None, description="Source or origin")
    applications: List[str] = Field(default_factory=list, description="Applications and uses")
    related_formulas: List[str] = Field(default_factory=list, description="Related formula IDs")
    page_number: int = Field(..., description="Page number where formula appears")
    context: str = Field(..., description="Surrounding context")


class Exercise(BaseModel):
    """Exercise structure"""
    id: str = Field(..., description="Unique exercise identifier")
    question: str = Field(..., description="Exercise question")
    type: ExerciseType = Field(..., description="Exercise type")
    formula_ids: List[str] = Field(default_factory=list, description="Related formula IDs")
    topic_ids: List[str] = Field(default_factory=list, description="Related topic IDs")
    solution: Optional[str] = Field(None, description="Solution explanation")
    difficulty: int = Field(default=1, ge=1, le=5, description="Difficulty level (1-5)")
    hints: List[str] = Field(default_factory=list, description="Hints for solving")


class NoteSection(BaseModel):
    """Note section structure"""
    id: str = Field(..., description="Unique section identifier")
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content in Markdown")
    topic_id: str = Field(..., description="Associated topic ID")
    formulas: List[Formula] = Field(default_factory=list, description="Formulas in this section")
    exercises: List[Exercise] = Field(default_factory=list, description="Exercises for this section")
    order: int = Field(..., description="Section order in the document")


class GeneratedNotes(BaseModel):
    """Complete generated notes structure"""
    id: str = Field(..., description="Unique notes identifier")
    title: str = Field(..., description="Notes title")
    source_filename: str = Field(..., description="Source PDF filename")
    sections: List[NoteSection] = Field(default_factory=list, description="Note sections")
    comprehensive_exercises: List[Exercise] = Field(default_factory=list, description="Comprehensive exercises")
    summary: str = Field(..., description="Overall summary")
    created_at: str = Field(..., description="Creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ProcessingResult(BaseModel):
    """Processing result structure"""
    status: ProcessingStatus = Field(..., description="Processing status")
    filename: str = Field(..., description="Processed filename")
    progress: int = Field(default=0, ge=0, le=100, description="Progress percentage")
    message: str = Field(default="", description="Status message")
    notes_id: Optional[str] = Field(None, description="Generated notes ID")
    error: Optional[str] = Field(None, description="Error message if failed")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")


class AgentState(BaseModel):
    """LangGraph agent state"""
    pdf_content: Optional[PDFContent] = Field(None, description="Extracted PDF content")
    topics: List[Topic] = Field(default_factory=list, description="Identified topics")
    formulas: List[Formula] = Field(default_factory=list, description="Extracted formulas")
    exercises: List[Exercise] = Field(default_factory=list, description="Generated exercises")
    notes: Optional[GeneratedNotes] = Field(None, description="Generated notes")
    current_step: str = Field(default="start", description="Current processing step")
    error: Optional[str] = Field(None, description="Error message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")


class UploadResponse(BaseModel):
    """File upload response"""
    message: str = Field(..., description="Response message")
    filename: str = Field(..., description="Uploaded filename")
    file_path: str = Field(..., description="File path")
    file_size: int = Field(..., description="File size in bytes")


class ProcessRequest(BaseModel):
    """Processing request"""
    filename: str = Field(..., description="Filename to process")
    options: Dict[str, Any] = Field(default_factory=dict, description="Processing options")


class StatusResponse(BaseModel):
    """Status check response"""
    filename: str = Field(..., description="Filename")
    status: ProcessingStatus = Field(..., description="Current status")
    progress: int = Field(..., description="Progress percentage")
    message: str = Field(..., description="Status message")
    estimated_time: Optional[int] = Field(None, description="Estimated remaining time in seconds")

