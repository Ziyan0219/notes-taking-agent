"""
Enhanced Note Generator for high-quality, readable study notes
"""

import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import openai
import os

@dataclass
class CleanFormula:
    """Clean, properly formatted formula"""
    name: str
    latex: str
    explanation: str
    applications: List[str]
    context: str

@dataclass
class CoreConcept:
    """Core concept with clear definition"""
    name: str
    definition: str
    key_terms: Dict[str, str]
    importance: str

@dataclass
class QualityExercise:
    """High-quality practice exercise"""
    title: str
    difficulty: int  # 1-4 stars
    question: str
    solution_approach: str
    concepts_used: List[str]

@dataclass
class StudySection:
    """Well-structured study section"""
    title: str
    core_concept: CoreConcept
    formulas: List[CleanFormula]
    exercises: List[QualityExercise]

class EnhancedNoteGenerator:
    """Enhanced note generator focused on clarity and utility"""
    
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        )
    
    def generate_quality_notes(self, topics: List[Dict], formulas: List[Dict], 
                             source_filename: str) -> str:
        """Generate high-quality study notes"""
        
        # Step 1: Clean and structure content
        clean_topics = self._clean_topics(topics)
        clean_formulas = self._clean_formulas(formulas)
        
        # Step 2: Generate study sections
        study_sections = self._generate_study_sections(clean_topics, clean_formulas)
        
        # Step 3: Create comprehensive exercises
        comprehensive_exercises = self._generate_comprehensive_exercises(study_sections)
        
        # Step 4: Format as beautiful markdown
        markdown_content = self._format_as_markdown(
            study_sections, comprehensive_exercises, source_filename
        )
        
        return markdown_content
    
    def _clean_topics(self, topics: List[Dict]) -> List[CoreConcept]:
        """Clean and enhance topic definitions"""
        clean_topics = []
        
        for topic in topics:
            try:
                # Use AI to clean and enhance the concept
                prompt = f"""
                Clean and enhance this concept definition for a study guide:
                
                Topic: {topic.get('title', 'Unknown')}
                Raw Definition: {topic.get('content', '')}
                
                Requirements:
                1. Create a clear, concise definition (1-2 sentences)
                2. Extract 3-5 key terms with brief definitions
                3. Explain why this concept is important
                4. Use simple, clear language
                5. Focus on practical understanding
                
                Return JSON format:
                {{
                    "definition": "clear definition",
                    "key_terms": {{"term1": "definition1", "term2": "definition2"}},
                    "importance": "why this matters"
                }}
                """
                
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                
                result = json.loads(response.choices[0].message.content)
                
                clean_concept = CoreConcept(
                    name=topic.get('title', 'Unknown'),
                    definition=result['definition'],
                    key_terms=result['key_terms'],
                    importance=result['importance']
                )
                
                clean_topics.append(clean_concept)
                
            except Exception as e:
                print(f"Error cleaning topic {topic.get('title', 'Unknown')}: {e}")
                continue
        
        return clean_topics
    
    def _clean_formulas(self, formulas: List[Dict]) -> List[CleanFormula]:
        """Clean and fix formula formatting"""
        clean_formulas = []
        
        for formula in formulas:
            try:
                # Use AI to fix and enhance the formula
                prompt = f"""
                Fix and enhance this mathematical formula for a study guide:
                
                Formula Name: {formula.get('name', 'Unknown')}
                Raw LaTeX: {formula.get('latex', '')}
                Raw Explanation: {formula.get('explanation', '')}
                Context: {formula.get('context', '')}
                
                Requirements:
                1. Fix LaTeX syntax errors (remove !, #, incomplete expressions)
                2. Create a clear, intuitive explanation
                3. List 2-3 practical applications
                4. Ensure mathematical accuracy
                5. Use proper mathematical notation
                
                Return JSON format:
                {{
                    "latex": "correct LaTeX formula",
                    "explanation": "clear explanation of what it means",
                    "applications": ["application1", "application2", "application3"]
                }}
                """
                
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )
                
                result = json.loads(response.choices[0].message.content)
                
                clean_formula = CleanFormula(
                    name=formula.get('name', 'Unknown Formula'),
                    latex=result['latex'],
                    explanation=result['explanation'],
                    applications=result['applications'],
                    context=formula.get('context', '')
                )
                
                clean_formulas.append(clean_formula)
                
            except Exception as e:
                print(f"Error cleaning formula {formula.get('name', 'Unknown')}: {e}")
                continue
        
        return clean_formulas
    
    def _generate_study_sections(self, topics: List[CoreConcept], 
                               formulas: List[CleanFormula]) -> List[StudySection]:
        """Generate well-structured study sections"""
        sections = []
        
        # Group formulas by topic
        for topic in topics:
            related_formulas = self._find_related_formulas(topic, formulas)
            
            if related_formulas:  # Only create sections with formulas
                # Generate quality exercises for this section
                exercises = self._generate_section_exercises(topic, related_formulas)
                
                section = StudySection(
                    title=topic.name,
                    core_concept=topic,
                    formulas=related_formulas,
                    exercises=exercises
                )
                
                sections.append(section)
        
        return sections
    
    def _find_related_formulas(self, topic: CoreConcept, 
                             formulas: List[CleanFormula]) -> List[CleanFormula]:
        """Find formulas related to a topic"""
        related = []
        topic_keywords = topic.name.lower().split()
        
        for formula in formulas:
            formula_text = (formula.name + " " + formula.explanation).lower()
            
            # Check for keyword overlap
            if any(keyword in formula_text for keyword in topic_keywords):
                related.append(formula)
        
        return related
    
    def _generate_section_exercises(self, topic: CoreConcept, 
                                  formulas: List[CleanFormula]) -> List[QualityExercise]:
        """Generate quality exercises for a section"""
        exercises = []
        
        try:
            # Create context for exercise generation
            formulas_text = "\n".join([
                f"- {f.name}: {f.latex} ({f.explanation})"
                for f in formulas
            ])
            
            prompt = f"""
            Generate 3 high-quality practice exercises for this study section:
            
            Topic: {topic.name}
            Definition: {topic.definition}
            Formulas:
            {formulas_text}
            
            Requirements:
            1. Basic Application (⭐⭐): Test formula understanding with realistic numbers
            2. Intermediate Application (⭐⭐⭐): Multi-step problem, assignment-level difficulty
            3. Advanced Application (⭐⭐⭐⭐): Complex scenario requiring deep understanding
            
            For each exercise:
            - Create a realistic, practical scenario
            - Provide clear problem statement
            - Include solution approach (not full solution)
            - Make it challenging but solvable
            
            Return JSON format:
            {{
                "exercises": [
                    {{
                        "title": "exercise title",
                        "difficulty": 2,
                        "question": "detailed question",
                        "solution_approach": "step-by-step approach"
                    }}
                ]
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )
            
            result = json.loads(response.choices[0].message.content)
            
            for ex_data in result['exercises']:
                exercise = QualityExercise(
                    title=ex_data['title'],
                    difficulty=ex_data['difficulty'],
                    question=ex_data['question'],
                    solution_approach=ex_data['solution_approach'],
                    concepts_used=[topic.name]
                )
                exercises.append(exercise)
                
        except Exception as e:
            print(f"Error generating exercises for {topic.name}: {e}")
        
        return exercises
    
    def _generate_comprehensive_exercises(self, sections: List[StudySection]) -> List[QualityExercise]:
        """Generate comprehensive exercises combining multiple concepts"""
        comprehensive_exercises = []
        
        if len(sections) < 2:
            return comprehensive_exercises
        
        try:
            # Create context from all sections
            sections_summary = "\n".join([
                f"- {s.title}: {s.core_concept.definition}"
                for s in sections
            ])
            
            all_formulas = []
            for section in sections:
                all_formulas.extend(section.formulas)
            
            formulas_summary = "\n".join([
                f"- {f.name}: {f.latex}"
                for f in all_formulas[:10]  # Limit to avoid token overflow
            ])
            
            prompt = f"""
            Generate 2 comprehensive exercises that combine multiple concepts:
            
            Available Concepts:
            {sections_summary}
            
            Key Formulas:
            {formulas_summary}
            
            Requirements:
            1. Integration Challenge (⭐⭐⭐⭐): Combine 2-3 concepts in realistic scenario
            2. Mastery Challenge (⭐⭐⭐⭐⭐): Complex problem requiring deep understanding
            
            For each exercise:
            - Create realistic, practical scenarios
            - Require multiple concepts/formulas
            - Assignment or exam level difficulty
            - Provide comprehensive solution approach
            
            Return JSON format:
            {{
                "exercises": [
                    {{
                        "title": "exercise title",
                        "difficulty": 4,
                        "question": "detailed question",
                        "solution_approach": "comprehensive approach"
                    }}
                ]
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )
            
            result = json.loads(response.choices[0].message.content)
            
            for ex_data in result['exercises']:
                exercise = QualityExercise(
                    title=ex_data['title'],
                    difficulty=ex_data['difficulty'],
                    question=ex_data['question'],
                    solution_approach=ex_data['solution_approach'],
                    concepts_used=[s.title for s in sections]
                )
                comprehensive_exercises.append(exercise)
                
        except Exception as e:
            print(f"Error generating comprehensive exercises: {e}")
        
        return comprehensive_exercises
    
    def _format_as_markdown(self, sections: List[StudySection], 
                          comprehensive_exercises: List[QualityExercise],
                          source_filename: str) -> str:
        """Format as beautiful, clean markdown"""
        
        # Header
        markdown = f"""# 📚 Study Notes: {source_filename}

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*

## 📋 Quick Overview

This study guide covers {len(sections)} main topics with {sum(len(s.formulas) for s in sections)} key formulas and {sum(len(s.exercises) for s in sections) + len(comprehensive_exercises)} practice exercises.

**Topics Covered:**
{chr(10).join([f"- **{s.title}**: {s.core_concept.definition}" for s in sections])}

---

"""
        
        # Table of Contents
        markdown += "## 📖 Table of Contents\n\n"
        for i, section in enumerate(sections, 1):
            markdown += f"{i}. [{section.title}](#{section.title.lower().replace(' ', '-')})\n"
        markdown += f"{len(sections) + 1}. [Comprehensive Exercises](#comprehensive-exercises)\n\n"
        markdown += "---\n\n"
        
        # Sections
        for section in sections:
            markdown += self._format_section(section)
            markdown += "\n---\n\n"
        
        # Comprehensive exercises
        if comprehensive_exercises:
            markdown += "## 🎯 Comprehensive Exercises\n\n"
            markdown += "*These exercises combine multiple concepts and test integrated understanding.*\n\n"
            
            for i, exercise in enumerate(comprehensive_exercises, 1):
                stars = "⭐" * exercise.difficulty
                markdown += f"### Exercise {i}: {exercise.title} {stars}\n\n"
                markdown += f"**Problem**: {exercise.question}\n\n"
                markdown += f"**Solution Approach**:\n{exercise.solution_approach}\n\n"
                markdown += f"**Concepts Used**: {', '.join(exercise.concepts_used)}\n\n"
        
        return markdown
    
    def _format_section(self, section: StudySection) -> str:
        """Format a single study section"""
        markdown = f"# {section.title}\n\n"
        
        # Core concept
        markdown += "## 📋 Core Concept\n\n"
        markdown += f"{section.core_concept.definition}\n\n"
        markdown += f"**Why it matters**: {section.core_concept.importance}\n\n"
        
        # Key terms
        if section.core_concept.key_terms:
            markdown += "## 🔑 Key Terms\n\n"
            for term, definition in section.core_concept.key_terms.items():
                markdown += f"- **{term}**: {definition}\n"
            markdown += "\n"
        
        # Formulas
        if section.formulas:
            markdown += "## 📐 Important Formulas\n\n"
            for formula in section.formulas:
                markdown += f"### {formula.name}\n\n"
                markdown += f"**Formula**: ${formula.latex}$\n\n"
                markdown += f"**Intuitive Understanding**: {formula.explanation}\n\n"
                markdown += "**Applications**:\n"
                for app in formula.applications:
                    markdown += f"- {app}\n"
                markdown += "\n"
        
        # Exercises
        if section.exercises:
            markdown += "## 💪 Practice Exercises\n\n"
            for i, exercise in enumerate(section.exercises, 1):
                stars = "⭐" * exercise.difficulty
                markdown += f"### Exercise {i}: {exercise.title} {stars}\n\n"
                markdown += f"**Problem**: {exercise.question}\n\n"
                markdown += f"<details>\n<summary>💡 Solution Approach</summary>\n\n"
                markdown += f"{exercise.solution_approach}\n\n</details>\n\n"
        
        return markdown

