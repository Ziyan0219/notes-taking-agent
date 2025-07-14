"""
LangGraph Agent for PDF to Notes conversion
"""

import logging
from typing import Dict, Any, List, Optional, List
from pathlib import Path
import json

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from openai import OpenAI

from app.models.schemas import (
    AgentState, PDFContent, Topic, Formula, Exercise, 
    GeneratedNotes, NoteSection, ProcessingStatus
)
from app.services.pdf_parser import PDFParser
from app.services.content_analyzer import ContentAnalyzer
from app.utils.helpers import generate_unique_id, get_timestamp

logger = logging.getLogger(__name__)


class NotesAgent:
    """LangGraph agent for converting PDF to structured notes"""
    
    def __init__(self, openai_api_key: str, model: str = "gpt-3.5-turbo"):
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.llm = ChatOpenAI(
            model=model,
            temperature=0.3,
            openai_api_key=openai_api_key
        )
        
        self.pdf_parser = PDFParser()
        self.content_analyzer = ContentAnalyzer(self.openai_client)
        
        # Build the agent graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("parse_pdf", self._parse_pdf_node)
        workflow.add_node("analyze_structure", self._analyze_structure_node)
        workflow.add_node("extract_formulas", self._extract_formulas_node)
        workflow.add_node("generate_notes", self._generate_notes_node)
        workflow.add_node("create_exercises", self._create_exercises_node)
        workflow.add_node("create_comprehensive_exercises", self._create_comprehensive_exercises_node)
        workflow.add_node("finalize_notes", self._finalize_notes_node)
        
        # Set entry point
        workflow.set_entry_point("parse_pdf")
        
        # Add edges
        workflow.add_edge("parse_pdf", "analyze_structure")
        workflow.add_edge("analyze_structure", "extract_formulas")
        workflow.add_edge("extract_formulas", "generate_notes")
        workflow.add_edge("generate_notes", "create_exercises")
        workflow.add_edge("create_exercises", "create_comprehensive_exercises")
        workflow.add_edge("create_comprehensive_exercises", "finalize_notes")
        workflow.add_edge("finalize_notes", END)
        
        return workflow.compile()
    
    async def process_pdf(self, file_path: Path, filename: str) -> AgentState:
        """
        Process PDF file through the agent workflow
        
        Args:
            file_path: Path to the PDF file
            filename: Original filename
            
        Returns:
            Final agent state with generated notes
        """
        logger.info(f"Starting PDF processing for: {filename}")
        
        # Initialize state
        initial_state = AgentState(
            current_step="start",
            metadata={
                "file_path": str(file_path),
                "filename": filename,
                "start_time": get_timestamp()
            }
        )
        
        try:
            # Run the workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            logger.info(f"PDF processing completed for: {filename}")
            return final_state
            
        except Exception as e:
            logger.error(f"Error processing PDF {filename}: {e}")
            initial_state.error = str(e)
            initial_state.current_step = "error"
            return initial_state
    
    def _parse_pdf_node(self, state: AgentState) -> AgentState:
        """Parse PDF and extract content"""
        
        logger.info("Parsing PDF content...")
        state.current_step = "parsing_pdf"
        
        try:
            file_path = Path(state.metadata["file_path"])
            pdf_content = self.pdf_parser.parse_pdf(file_path)
            
            state.pdf_content = pdf_content
            logger.info(f"PDF parsed successfully. Pages: {pdf_content.pages}, "
                       f"Text length: {len(pdf_content.text)}")
            
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            state.error = f"PDF parsing failed: {str(e)}"
        
        return state
    
    def _analyze_structure_node(self, state: AgentState) -> AgentState:
        """Analyze document structure and identify topics"""
        
        logger.info("Analyzing document structure...")
        state.current_step = "analyzing_structure"
        
        try:
            if not state.pdf_content:
                raise ValueError("No PDF content available")
            
            topics = self.content_analyzer.analyze_document_structure(state.pdf_content)
            state.topics = topics
            
            logger.info(f"Identified {len(topics)} topics")
            
        except Exception as e:
            logger.error(f"Error analyzing structure: {e}")
            state.error = f"Structure analysis failed: {str(e)}"
        
        return state
    
    def _extract_formulas_node(self, state: AgentState) -> AgentState:
        """Extract and analyze formulas"""
        
        logger.info("Extracting formulas...")
        state.current_step = "extracting_formulas"
        
        try:
            if not state.pdf_content or not state.topics:
                raise ValueError("Missing PDF content or topics")
            
            formulas = self.content_analyzer.extract_formulas(state.pdf_content, state.topics)
            state.formulas = formulas
            
            logger.info(f"Extracted {len(formulas)} formulas")
            
        except Exception as e:
            logger.error(f"Error extracting formulas: {e}")
            state.error = f"Formula extraction failed: {str(e)}"
        
        return state
    
    def _generate_notes_node(self, state: AgentState) -> AgentState:
        """Generate structured notes"""
        
        logger.info("Generating structured notes...")
        state.current_step = "generating_notes"
        
        try:
            if not state.topics or not state.formulas:
                raise ValueError("Missing topics or formulas")
            
            notes = self._create_structured_notes(state.topics, state.formulas, state.metadata["filename"])
            state.notes = notes
            
            logger.info(f"Generated notes with {len(notes.sections)} sections")
            
        except Exception as e:
            logger.error(f"Error generating notes: {e}")
            state.error = f"Notes generation failed: {str(e)}"
        
        return state
    
    def _create_exercises_node(self, state: AgentState) -> AgentState:
        """Create exercises for each formula"""
        
        logger.info("Creating exercises...")
        state.current_step = "creating_exercises"
        
        try:
            if not state.formulas:
                raise ValueError("No formulas available for exercise creation")
            
            exercises = self._generate_formula_exercises(state.formulas, state.topics)
            state.exercises = exercises
            
            logger.info(f"Created {len(exercises)} exercises")
            
        except Exception as e:
            logger.error(f"Error creating exercises: {e}")
            state.error = f"Exercise creation failed: {str(e)}"
        
        return state
    
    def _create_comprehensive_exercises_node(self, state: AgentState) -> AgentState:
        """Create comprehensive exercises combining multiple concepts"""
        
        logger.info("Creating comprehensive exercises...")
        state.current_step = "creating_comprehensive_exercises"
        
        try:
            if not state.formulas or not state.topics:
                raise ValueError("Missing formulas or topics for comprehensive exercises")
            
            comprehensive_exercises = self._generate_comprehensive_exercises(
                state.formulas, state.topics
            )
            
            # Add to notes
            if state.notes:
                state.notes.comprehensive_exercises = comprehensive_exercises
            
            logger.info(f"Created {len(comprehensive_exercises)} comprehensive exercises")
            
        except Exception as e:
            logger.error(f"Error creating comprehensive exercises: {e}")
            state.error = f"Comprehensive exercise creation failed: {str(e)}"
        
        return state
    
    def _finalize_notes_node(self, state: AgentState) -> AgentState:
        """Finalize and validate the generated notes"""
        
        logger.info("Finalizing notes...")
        state.current_step = "finalizing"
        
        try:
            if not state.notes:
                raise ValueError("No notes to finalize")
            
            # Add exercises to note sections
            self._add_exercises_to_sections(state.notes, state.exercises)
            
            # Generate summary
            state.notes.summary = self._generate_summary(state.notes)
            
            # Update metadata
            state.metadata["end_time"] = get_timestamp()
            state.metadata["total_topics"] = len(state.topics)
            state.metadata["total_formulas"] = len(state.formulas)
            state.metadata["total_exercises"] = len(state.exercises)
            
            state.current_step = "completed"
            logger.info("Notes finalization completed")
            
        except Exception as e:
            logger.error(f"Error finalizing notes: {e}")
            state.error = f"Notes finalization failed: {str(e)}"
        
        return state
    
    def _create_structured_notes(self, topics: List[Topic], formulas: List[Formula], 
                                filename: str) -> GeneratedNotes:
        """Create structured notes from topics and formulas"""
        
        notes_id = generate_unique_id("notes")
        sections = []
        
        # Group formulas by topic
        topic_formulas = {}
        for formula in formulas:
            if formula.topic_id not in topic_formulas:
                topic_formulas[formula.topic_id] = []
            topic_formulas[formula.topic_id].append(formula)
        
        # Create sections for each topic
        for idx, topic in enumerate(topics):
            topic_formulas_list = topic_formulas.get(topic.id, [])
            
            # Generate section content
            section_content = self._generate_section_content(topic, topic_formulas_list)
            
            section = NoteSection(
                id=f"section_{idx + 1}",
                title=topic.title,
                content=section_content,
                topic_id=topic.id,
                formulas=topic_formulas_list,
                exercises=[],  # Will be added later
                order=idx + 1
            )
            
            sections.append(section)
        
        return GeneratedNotes(
            id=notes_id,
            title=f"Study Notes - {filename}",
            source_filename=filename,
            sections=sections,
            comprehensive_exercises=[],
            summary="",  # Will be generated later
            created_at=get_timestamp(),
            metadata={}
        )
    
    def _generate_section_content(self, topic: Topic, formulas: List[Formula]) -> str:
        """Generate content for a note section"""
        
        content_parts = []
        
        # Add topic introduction
        content_parts.append(f"## {topic.title}\n")
        
        if topic.content:
            content_parts.append(f"{topic.content}\n")
        
        # Add keywords if available
        if topic.keywords:
            keywords_str = ", ".join(topic.keywords)
            content_parts.append(f"**Key Terms**: {keywords_str}\n")
        
        # Add formulas
        if formulas:
            content_parts.append("### Key Formulas\n")
            
            for formula in formulas:
                content_parts.append(f"#### {formula.name}\n")
                content_parts.append(f"**Formula**: ${formula.latex}$\n")
                
                if formula.derivation:
                    content_parts.append(f"**Explanation**: {formula.derivation}\n")
                
                if formula.applications:
                    apps_str = ", ".join(formula.applications)
                    content_parts.append(f"**Applications**: {apps_str}\n")
                
                if formula.context:
                    content_parts.append(f"> **Context**: {formula.context[:200]}...\n")
                
                content_parts.append("")  # Empty line
        
        return "\n".join(content_parts)
    
    def _generate_formula_exercises(self, formulas: List[Formula], topics: List[Topic]) -> List[Exercise]:
        """Generate exercises for formulas"""
        
        exercises = []
        
        # Process formulas in batches to optimize API calls
        batch_size = 3
        
        for i in range(0, len(formulas), batch_size):
            batch = formulas[i:i + batch_size]
            
            try:
                batch_exercises = self._create_exercise_batch(batch, topics)
                exercises.extend(batch_exercises)
                
            except Exception as e:
                logger.warning(f"Failed to create exercises for batch {i//batch_size}: {e}")
                
                # Create fallback exercises
                for formula in batch:
                    fallback_exercise = Exercise(
                        id=generate_unique_id("exercise"),
                        question=f"Apply the formula {formula.name}: ${formula.latex}$ to solve a practical problem.",
                        type="simple_application",
                        formula_ids=[formula.id],
                        topic_ids=[formula.topic_id],
                        difficulty=2
                    )
                    exercises.append(fallback_exercise)
        
        return exercises
    
    def _create_exercise_batch(self, formulas: List[Formula], topics: List[Topic]) -> List[Exercise]:
        """Create exercises for a batch of formulas using AI"""
        
        # Prepare context
        formula_info = []
        for formula in formulas:
            formula_info.append({
                "id": formula.id,
                "name": formula.name,
                "latex": formula.latex,
                "type": formula.type,
                "context": formula.context[:200] if formula.context else ""
            })
        
        topic_info = {topic.id: topic.title for topic in topics}
        
        prompt = f"""
Create practice exercises for the following mathematical formulas. Each exercise should be practical and help students understand the formula's application.

Formulas:
{json.dumps(formula_info, indent=2)}

Topics:
{json.dumps(topic_info, indent=2)}

For each formula, create one exercise with:
1. A clear, practical question
2. Appropriate difficulty level (1-5)
3. Brief solution approach (optional)

Return your response in JSON format:
{{
    "exercises": [
        {{
            "formula_id": "formula_id",
            "question": "Exercise question",
            "difficulty": 1-5,
            "solution_approach": "Brief solution approach"
        }}
    ]
}}
"""
        
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert educator creating practice exercises for mathematical concepts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        # Parse response
        exercises = []
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response.choices[0].message.content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                for exercise_data in data.get('exercises', []):
                    formula_id = exercise_data.get('formula_id')
                    formula = next((f for f in formulas if f.id == formula_id), None)
                    
                    if formula:
                        exercise = Exercise(
                            id=generate_unique_id("exercise"),
                            question=exercise_data.get('question', ''),
                            type="simple_application",
                            formula_ids=[formula.id],
                            topic_ids=[formula.topic_id],
                            solution=exercise_data.get('solution_approach'),
                            difficulty=exercise_data.get('difficulty', 2)
                        )
                        exercises.append(exercise)
                        
        except Exception as e:
            logger.warning(f"Failed to parse exercise response: {e}")
        
        return exercises
    
    def _generate_comprehensive_exercises(self, formulas: List[Formula], 
                                        topics: List[Topic]) -> List[Exercise]:
        """Generate comprehensive exercises combining multiple concepts"""
        
        if len(formulas) < 2:
            return []
        
        try:
            # Select formulas from different topics for comprehensive exercises
            topic_formulas = {}
            for formula in formulas:
                if formula.topic_id not in topic_formulas:
                    topic_formulas[formula.topic_id] = []
                topic_formulas[formula.topic_id].append(formula)
            
            # Create 2 comprehensive exercises
            comprehensive_exercises = []
            
            # Exercise 1: Combine formulas from first two topics
            topic_ids = list(topic_formulas.keys())
            if len(topic_ids) >= 2:
                selected_formulas = []
                selected_formulas.extend(topic_formulas[topic_ids[0]][:2])
                selected_formulas.extend(topic_formulas[topic_ids[1]][:2])
                
                exercise1 = self._create_comprehensive_exercise(selected_formulas, topics, 1)
                if exercise1:
                    comprehensive_exercises.append(exercise1)
            
            # Exercise 2: Combine different formulas
            if len(formulas) >= 3:
                selected_formulas = formulas[:3]
                exercise2 = self._create_comprehensive_exercise(selected_formulas, topics, 2)
                if exercise2:
                    comprehensive_exercises.append(exercise2)
            
            return comprehensive_exercises
            
        except Exception as e:
            logger.warning(f"Failed to create comprehensive exercises: {e}")
            return []
    
    def _create_comprehensive_exercise(self, formulas: List[Formula], 
                                     topics: List[Topic], exercise_num: int) -> Optional[Exercise]:
        """Create a single comprehensive exercise"""
        
        try:
            formula_info = [{"name": f.name, "latex": f.latex} for f in formulas]
            topic_titles = [t.title for t in topics if t.id in [f.topic_id for f in formulas]]
            
            prompt = f"""
Create a comprehensive exercise that combines the following formulas and concepts:

Formulas: {json.dumps(formula_info, indent=2)}
Topics: {topic_titles}

Create a challenging problem that requires students to:
1. Apply multiple formulas
2. Understand relationships between concepts
3. Solve a realistic scenario

The exercise should be at difficulty level 4-5 and include a brief solution approach.

Return your response in JSON format:
{{
    "question": "Comprehensive exercise question",
    "solution_approach": "Step-by-step solution approach",
    "difficulty": 4
}}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert educator creating challenging comprehensive exercises."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            # Parse response
            import re
            json_match = re.search(r'\{.*\}', response.choices[0].message.content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                return Exercise(
                    id=generate_unique_id("comprehensive"),
                    question=data.get('question', ''),
                    type="comprehensive",
                    formula_ids=[f.id for f in formulas],
                    topic_ids=list(set(f.topic_id for f in formulas)),
                    solution=data.get('solution_approach'),
                    difficulty=data.get('difficulty', 4)
                )
                
        except Exception as e:
            logger.warning(f"Failed to create comprehensive exercise {exercise_num}: {e}")
        
        return None
    
    def _add_exercises_to_sections(self, notes: GeneratedNotes, exercises: List[Exercise]):
        """Add exercises to appropriate note sections"""
        
        # Group exercises by topic
        topic_exercises = {}
        for exercise in exercises:
            for topic_id in exercise.topic_ids:
                if topic_id not in topic_exercises:
                    topic_exercises[topic_id] = []
                topic_exercises[topic_id].append(exercise)
        
        # Add exercises to sections
        for section in notes.sections:
            section_exercises = topic_exercises.get(section.topic_id, [])
            section.exercises = section_exercises
    
    def _generate_summary(self, notes: GeneratedNotes) -> str:
        """Generate a summary of the notes"""
        
        summary_parts = []
        
        summary_parts.append(f"This document contains {len(notes.sections)} main sections covering:")
        
        for section in notes.sections:
            formula_count = len(section.formulas)
            exercise_count = len(section.exercises)
            summary_parts.append(f"- {section.title}: {formula_count} formulas, {exercise_count} exercises")
        
        comprehensive_count = len(notes.comprehensive_exercises)
        if comprehensive_count > 0:
            summary_parts.append(f"\nAdditionally, {comprehensive_count} comprehensive exercises are provided to test integrated understanding.")
        
        return "\n".join(summary_parts)

