"""
Note generation service for creating structured study notes
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime

from app.models.schemas import (
    Topic, Formula, Exercise, GeneratedNotes, NoteSection,
    TopicType, FormulaType
)
from app.utils.helpers import generate_unique_id, get_timestamp

logger = logging.getLogger(__name__)


class NoteGenerator:
    """Service for generating structured study notes"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def generate_notes(self, topics: List[Topic], formulas: List[Formula], 
                      exercises: List[Exercise], source_filename: str) -> GeneratedNotes:
        """
        Generate structured notes from extracted content
        
        Args:
            topics: List of identified topics
            formulas: List of extracted formulas
            exercises: List of generated exercises
            source_filename: Original PDF filename
            
        Returns:
            Generated notes object
        """
        logger.info(f"Generating notes for {len(topics)} topics, {len(formulas)} formulas")
        
        # Create note sections
        sections = self._create_note_sections(topics, formulas, exercises)
        
        # Generate comprehensive exercises
        comprehensive_exercises = self._filter_comprehensive_exercises(exercises)
        
        # Create notes object
        notes = GeneratedNotes(
            id=generate_unique_id("notes"),
            title=self._generate_title(source_filename),
            source_filename=source_filename,
            sections=sections,
            comprehensive_exercises=comprehensive_exercises,
            summary=self._generate_summary(sections, comprehensive_exercises),
            created_at=get_timestamp(),
            metadata={
                "total_topics": len(topics),
                "total_formulas": len(formulas),
                "total_exercises": len(exercises),
                "generation_method": "ai_assisted"
            }
        )
        
        logger.info(f"Generated notes with {len(sections)} sections")
        return notes
    
    def _create_note_sections(self, topics: List[Topic], formulas: List[Formula], 
                             exercises: List[Exercise]) -> List[NoteSection]:
        """Create note sections from topics"""
        
        sections = []
        
        # Group formulas and exercises by topic
        topic_formulas = self._group_by_topic(formulas, lambda f: f.topic_id)
        topic_exercises = self._group_by_topic_list(exercises, lambda e: e.topic_ids)
        
        # Sort topics by level and order
        sorted_topics = sorted(topics, key=lambda t: (t.level, t.title))
        
        for idx, topic in enumerate(sorted_topics):
            # Get related formulas and exercises
            related_formulas = topic_formulas.get(topic.id, [])
            related_exercises = topic_exercises.get(topic.id, [])
            
            # Generate section content
            content = self._generate_section_content(topic, related_formulas)
            
            section = NoteSection(
                id=f"section_{idx + 1}",
                title=topic.title,
                content=content,
                topic_id=topic.id,
                formulas=related_formulas,
                exercises=related_exercises,
                order=idx + 1
            )
            
            sections.append(section)
        
        return sections
    
    def _generate_section_content(self, topic: Topic, formulas: List[Formula]) -> str:
        """Generate Markdown content for a section"""
        
        content_parts = []
        
        # Section header
        header_level = "#" * min(topic.level + 1, 6)  # Limit to h6
        content_parts.append(f"{header_level} {topic.title}\n")
        
        # Topic content
        if topic.content and topic.content.strip():
            content_parts.append(f"{topic.content}\n")
        
        # Keywords section
        if topic.keywords:
            content_parts.append("### Key Concepts")
            keywords_formatted = ", ".join([f"**{kw}**" for kw in topic.keywords])
            content_parts.append(f"{keywords_formatted}\n")
        
        # Formulas section
        if formulas:
            content_parts.append("### Important Formulas\n")
            
            for formula in formulas:
                content_parts.append(self._format_formula(formula))
        
        return "\n".join(content_parts)
    
    def _format_formula(self, formula: Formula) -> str:
        """Format a formula for display in notes"""
        
        parts = []
        
        # Formula name and equation
        parts.append(f"#### {formula.name}\n")
        parts.append(f"**Formula**: ${formula.latex}$\n")
        
        # Type indicator
        type_emoji = {
            FormulaType.EQUATION: "⚖️",
            FormulaType.THEOREM: "🔬",
            FormulaType.DEFINITION: "📖",
            FormulaType.PROPERTY: "🔍"
        }
        emoji = type_emoji.get(formula.type, "📐")
        parts.append(f"**Type**: {emoji} {formula.type.value.title()}\n")
        
        # Derivation/Explanation
        if formula.derivation:
            parts.append(f"**Explanation**: {formula.derivation}\n")
        
        # Applications
        if formula.applications:
            apps_text = ", ".join(formula.applications)
            parts.append(f"**Applications**: {apps_text}\n")
        
        # Context box (if available)
        if formula.context and len(formula.context) > 20:
            context_preview = formula.context[:150] + "..." if len(formula.context) > 150 else formula.context
            parts.append(f"> **Context**: {context_preview}\n")
        
        # Related formulas
        if formula.related_formulas:
            related_text = ", ".join(formula.related_formulas)
            parts.append(f"**Related**: {related_text}\n")
        
        parts.append("")  # Empty line for spacing
        
        return "\n".join(parts)
    
    def _filter_comprehensive_exercises(self, exercises: List[Exercise]) -> List[Exercise]:
        """Filter out comprehensive exercises from the main list"""
        
        return [ex for ex in exercises if ex.type == "comprehensive"]
    
    def _generate_title(self, source_filename: str) -> str:
        """Generate a title for the notes"""
        
        # Clean filename
        base_name = Path(source_filename).stem
        base_name = base_name.replace("_", " ").replace("-", " ")
        
        # Capitalize words
        title_words = []
        for word in base_name.split():
            if len(word) > 2:
                title_words.append(word.capitalize())
            else:
                title_words.append(word.upper())
        
        title = " ".join(title_words)
        
        return f"Study Notes: {title}"
    
    def _generate_summary(self, sections: List[NoteSection], 
                         comprehensive_exercises: List[Exercise]) -> str:
        """Generate a summary of the notes"""
        
        summary_parts = []
        
        # Overview
        total_formulas = sum(len(section.formulas) for section in sections)
        total_exercises = sum(len(section.exercises) for section in sections)
        
        summary_parts.append(f"This study guide covers {len(sections)} main topics with {total_formulas} key formulas and {total_exercises} practice exercises.")
        
        # Section breakdown
        if sections:
            summary_parts.append("\n**Topics Covered:**")
            for section in sections:
                formula_count = len(section.formulas)
                exercise_count = len(section.exercises)
                summary_parts.append(f"- **{section.title}**: {formula_count} formulas, {exercise_count} exercises")
        
        # Comprehensive exercises
        if comprehensive_exercises:
            summary_parts.append(f"\n**Additional Features:**")
            summary_parts.append(f"- {len(comprehensive_exercises)} comprehensive exercises for integrated practice")
        
        # Study recommendations
        summary_parts.append("\n**Study Recommendations:**")
        summary_parts.append("1. Review each topic's key concepts and formulas")
        summary_parts.append("2. Practice the exercises for each section")
        summary_parts.append("3. Complete comprehensive exercises to test integrated understanding")
        summary_parts.append("4. Focus on understanding derivations and applications")
        
        return "\n".join(summary_parts)
    
    def _group_by_topic(self, items: List, key_func) -> Dict[str, List]:
        """Group items by topic ID"""
        
        groups = {}
        for item in items:
            topic_id = key_func(item)
            if topic_id not in groups:
                groups[topic_id] = []
            groups[topic_id].append(item)
        
        return groups
    
    def _group_by_topic_list(self, items: List, key_func) -> Dict[str, List]:
        """Group items by multiple topic IDs"""
        
        groups = {}
        for item in items:
            topic_ids = key_func(item)
            for topic_id in topic_ids:
                if topic_id not in groups:
                    groups[topic_id] = []
                groups[topic_id].append(item)
        
        return groups
    
    def _load_templates(self) -> Dict[str, str]:
        """Load note templates"""
        
        templates = {
            "section_header": """
# {title}

{content}

## Key Concepts
{keywords}

## Important Formulas
{formulas}

## Practice Exercises
{exercises}
""",
            
            "formula_template": """
### {name}

**Formula**: ${latex}$

**Type**: {type}

{derivation}

{applications}

{context}
""",
            
            "exercise_template": """
**Exercise {number}** (Difficulty: {difficulty}/5)

{question}

{solution}
""",
            
            "comprehensive_template": """
## Comprehensive Exercise {number}

**Difficulty**: {difficulty}/5
**Topics**: {topics}

{question}

### Solution Approach
{solution}
"""
        }
        
        return templates
    
    def export_to_markdown(self, notes: GeneratedNotes) -> str:
        """Export notes to Markdown format"""
        
        # Check if this is enhanced content (already formatted)
        if (hasattr(notes, 'metadata') and 
            notes.metadata.get('generation_method') == 'enhanced'):
            # Enhanced generator already provides complete markdown
            return notes.content
        
        # Legacy format handling
        markdown_parts = []
        
        # Title and metadata
        markdown_parts.append(f"# {notes.title}\n")
        markdown_parts.append(f"**Source**: {notes.source_filename}")
        markdown_parts.append(f"**Generated**: {notes.created_at}")
        markdown_parts.append(f"**Total Sections**: {len(notes.sections)}")
        markdown_parts.append("")
        
        # Summary
        markdown_parts.append("## Summary\n")
        markdown_parts.append(f"{notes.summary}\n")
        
        # Table of Contents
        if len(notes.sections) > 1:
            markdown_parts.append("## Table of Contents\n")
            for section in notes.sections:
                markdown_parts.append(f"{section.order}. [{section.title}](#{self._create_anchor(section.title)})")
            markdown_parts.append("")
        
        # Sections
        for section in notes.sections:
            markdown_parts.append(section.content)
            
            # Add exercises for this section
            if section.exercises:
                markdown_parts.append("### Practice Exercises\n")
                
                for idx, exercise in enumerate(section.exercises, 1):
                    exercise_md = self._format_exercise_markdown(exercise, idx)
                    markdown_parts.append(exercise_md)
        
        # Comprehensive exercises
        if notes.comprehensive_exercises:
            markdown_parts.append("---\n")
            markdown_parts.append("## Comprehensive Exercises\n")
            markdown_parts.append("*These exercises combine concepts from multiple topics*\n")
            
            for idx, exercise in enumerate(notes.comprehensive_exercises, 1):
                comp_exercise_md = self._format_comprehensive_exercise_markdown(exercise, idx)
                markdown_parts.append(comp_exercise_md)
        
        # Footer
        markdown_parts.append("---")
        markdown_parts.append("*Generated by Notes Taking Agent*")
        
        return "\n".join(markdown_parts)
    
    def _format_exercise_markdown(self, exercise: Exercise, number: int) -> str:
        """Format exercise for Markdown export"""
        
        parts = []
        
        # Exercise header
        difficulty_stars = "⭐" * exercise.difficulty
        parts.append(f"#### Exercise {number} {difficulty_stars}\n")
        
        # Question
        parts.append(f"{exercise.question}\n")
        
        # Solution (if available)
        if exercise.solution:
            parts.append(f"<details>")
            parts.append(f"<summary>💡 Solution Approach</summary>\n")
            parts.append(f"{exercise.solution}\n")
            parts.append(f"</details>\n")
        
        return "\n".join(parts)
    
    def _format_comprehensive_exercise_markdown(self, exercise: Exercise, number: int) -> str:
        """Format comprehensive exercise for Markdown export"""
        
        parts = []
        
        # Exercise header
        difficulty_stars = "⭐" * exercise.difficulty
        parts.append(f"### Comprehensive Exercise {number} {difficulty_stars}\n")
        
        # Question
        parts.append(f"{exercise.question}\n")
        
        # Solution (if available)
        if exercise.solution:
            parts.append(f"#### Solution Approach\n")
            parts.append(f"{exercise.solution}\n")
        
        return "\n".join(parts)
    
    def _create_anchor(self, text: str) -> str:
        """Create anchor link for table of contents"""
        
        # Convert to lowercase and replace spaces with hyphens
        anchor = text.lower().replace(" ", "-")
        
        # Remove special characters
        import re
        anchor = re.sub(r'[^a-z0-9\-]', '', anchor)
        
        return anchor
    
    def export_to_json(self, notes: GeneratedNotes) -> str:
        """Export notes to JSON format"""
        
        return json.dumps(notes.dict(), indent=2, ensure_ascii=False)
    
    def create_study_plan(self, notes: GeneratedNotes, study_days: int = 7) -> str:
        """Create a study plan based on the notes"""
        
        plan_parts = []
        
        plan_parts.append(f"# Study Plan: {notes.title}\n")
        plan_parts.append(f"**Duration**: {study_days} days")
        plan_parts.append(f"**Total Topics**: {len(notes.sections)}\n")
        
        # Calculate topics per day
        topics_per_day = max(1, len(notes.sections) // study_days)
        
        current_day = 1
        current_topics = 0
        
        plan_parts.append("## Daily Schedule\n")
        
        for section in notes.sections:
            if current_topics == 0:
                plan_parts.append(f"### Day {current_day}\n")
            
            plan_parts.append(f"- **{section.title}**")
            plan_parts.append(f"  - Review {len(section.formulas)} formulas")
            plan_parts.append(f"  - Complete {len(section.exercises)} exercises")
            
            current_topics += 1
            
            if current_topics >= topics_per_day and current_day < study_days:
                current_topics = 0
                current_day += 1
                plan_parts.append("")
        
        # Add comprehensive exercises to final days
        if notes.comprehensive_exercises:
            plan_parts.append(f"\n### Final Review (Day {study_days})")
            plan_parts.append(f"- Complete {len(notes.comprehensive_exercises)} comprehensive exercises")
            plan_parts.append("- Review all formulas and concepts")
        
        return "\n".join(plan_parts)

