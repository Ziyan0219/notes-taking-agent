"""
Exercise generation service for creating practice questions
"""

import logging
from typing import List, Dict, Any, Optional
import json
import re
from openai import OpenAI

from app.models.schemas import (
    Formula, Topic, Exercise, ExerciseType, FormulaType
)
from app.utils.helpers import generate_unique_id

logger = logging.getLogger(__name__)


class ExerciseGenerator:
    """Service for generating practice exercises"""
    
    def __init__(self, openai_client: Optional[OpenAI] = None):
        self.client = openai_client or OpenAI()
        self.model = "gpt-3.5-turbo"
        
        # Exercise templates for different types
        self.templates = self._load_exercise_templates()
    
    def generate_formula_exercises(self, formulas: List[Formula], 
                                 topics: List[Topic]) -> List[Exercise]:
        """
        Generate exercises for individual formulas
        
        Args:
            formulas: List of formulas to create exercises for
            topics: List of topics for context
            
        Returns:
            List of generated exercises
        """
        logger.info(f"Generating exercises for {len(formulas)} formulas")
        
        exercises = []
        
        # Process formulas in batches to optimize API calls
        batch_size = 3
        
        for i in range(0, len(formulas), batch_size):
            batch = formulas[i:i + batch_size]
            
            try:
                batch_exercises = self._generate_batch_exercises(batch, topics)
                exercises.extend(batch_exercises)
                
            except Exception as e:
                logger.warning(f"Failed to generate exercises for batch {i//batch_size}: {e}")
                
                # Create fallback exercises
                for formula in batch:
                    fallback_exercise = self._create_fallback_exercise(formula)
                    exercises.append(fallback_exercise)
        
        logger.info(f"Generated {len(exercises)} formula exercises")
        return exercises
    
    def generate_comprehensive_exercises(self, formulas: List[Formula], 
                                       topics: List[Topic], count: int = 2) -> List[Exercise]:
        """
        Generate comprehensive exercises combining multiple concepts
        
        Args:
            formulas: List of available formulas
            topics: List of topics
            count: Number of comprehensive exercises to generate
            
        Returns:
            List of comprehensive exercises
        """
        logger.info(f"Generating {count} comprehensive exercises")
        
        if len(formulas) < 2:
            logger.warning("Not enough formulas for comprehensive exercises")
            return []
        
        exercises = []
        
        # Select diverse formulas for comprehensive exercises
        selected_formula_sets = self._select_formula_combinations(formulas, topics, count)
        
        for idx, formula_set in enumerate(selected_formula_sets):
            try:
                exercise = self._generate_comprehensive_exercise(formula_set, topics, idx + 1)
                if exercise:
                    exercises.append(exercise)
                    
            except Exception as e:
                logger.warning(f"Failed to generate comprehensive exercise {idx + 1}: {e}")
        
        logger.info(f"Generated {len(exercises)} comprehensive exercises")
        return exercises
    
    def generate_conceptual_exercises(self, topics: List[Topic]) -> List[Exercise]:
        """
        Generate conceptual understanding exercises
        
        Args:
            topics: List of topics
            
        Returns:
            List of conceptual exercises
        """
        logger.info(f"Generating conceptual exercises for {len(topics)} topics")
        
        exercises = []
        
        for topic in topics[:3]:  # Limit to first 3 topics
            try:
                exercise = self._generate_conceptual_exercise(topic)
                if exercise:
                    exercises.append(exercise)
                    
            except Exception as e:
                logger.warning(f"Failed to generate conceptual exercise for {topic.title}: {e}")
        
        return exercises
    
    def _generate_batch_exercises(self, formulas: List[Formula], 
                                topics: List[Topic]) -> List[Exercise]:
        """Generate exercises for a batch of formulas using AI"""
        
        # Prepare context
        formula_info = []
        for formula in formulas:
            formula_info.append({
                "id": formula.id,
                "name": formula.name,
                "latex": formula.latex,
                "type": formula.type.value,
                "derivation": formula.derivation[:200] if formula.derivation else "",
                "applications": formula.applications[:3] if formula.applications else [],
                "context": formula.context[:150] if formula.context else ""
            })
        
        topic_context = {topic.id: {"title": topic.title, "keywords": topic.keywords[:5]} 
                        for topic in topics}
        
        prompt = self._create_exercise_generation_prompt(formula_info, topic_context)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert educator creating practice exercises for mathematical concepts. Create engaging, practical problems that help students understand and apply formulas."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Parse response and create Exercise objects
        exercises = self._parse_exercise_response(response.choices[0].message.content, formulas)
        
        return exercises
    
    def _create_exercise_generation_prompt(self, formula_info: List[Dict], 
                                         topic_context: Dict[str, Dict]) -> str:
        """Create prompt for exercise generation"""
        
        prompt = f"""
Create practice exercises for the following mathematical formulas. Each exercise should be practical, engaging, and help students understand the formula's application.

Formulas to create exercises for:
{json.dumps(formula_info, indent=2)}

Topic context:
{json.dumps(topic_context, indent=2)}

For each formula, create ONE exercise with the following requirements:
1. **Practical Application**: Use real-world scenarios when possible
2. **Clear Question**: State the problem clearly with given values
3. **Appropriate Difficulty**: Match the complexity to the formula type
4. **Solution Guidance**: Provide hints or solution approach
5. **Educational Value**: Help students understand the concept

Exercise types to consider:
- **Calculation**: Direct application of the formula
- **Problem Solving**: Multi-step problems using the formula
- **Conceptual**: Understanding what the formula represents
- **Comparison**: Comparing results using different parameters

Return your response in JSON format:
{{
    "exercises": [
        {{
            "formula_id": "formula_id",
            "question": "Clear, practical exercise question with specific values",
            "exercise_type": "calculation|problem_solving|conceptual|comparison",
            "difficulty": 1-5,
            "solution_approach": "Step-by-step solution guidance",
            "hints": ["hint1", "hint2"],
            "real_world_context": "Brief description of real-world relevance"
        }}
    ]
}}

Make sure each exercise is unique and tests different aspects of formula application.
"""
        
        return prompt
    
    def _parse_exercise_response(self, response_content: str, 
                               formulas: List[Formula]) -> List[Exercise]:
        """Parse AI response and create Exercise objects"""
        
        exercises = []
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in response")
            
            data = json.loads(json_match.group())
            
            for exercise_data in data.get('exercises', []):
                formula_id = exercise_data.get('formula_id')
                formula = next((f for f in formulas if f.id == formula_id), None)
                
                if not formula:
                    continue
                
                # Map exercise type
                exercise_type = ExerciseType.SIMPLE_APPLICATION
                type_str = exercise_data.get('exercise_type', 'calculation').lower()
                
                if 'conceptual' in type_str:
                    exercise_type = ExerciseType.CONCEPTUAL
                elif 'problem' in type_str or 'solving' in type_str:
                    exercise_type = ExerciseType.SIMPLE_APPLICATION
                
                # Create exercise
                exercise = Exercise(
                    id=generate_unique_id("exercise"),
                    question=exercise_data.get('question', ''),
                    type=exercise_type,
                    formula_ids=[formula.id],
                    topic_ids=[formula.topic_id],
                    solution=exercise_data.get('solution_approach', ''),
                    difficulty=exercise_data.get('difficulty', 2),
                    hints=exercise_data.get('hints', [])
                )
                
                exercises.append(exercise)
                
        except Exception as e:
            logger.warning(f"Failed to parse exercise response: {e}")
        
        return exercises
    
    def _create_fallback_exercise(self, formula: Formula) -> Exercise:
        """Create a simple fallback exercise for a formula"""
        
        # Determine exercise type based on formula type
        if formula.type == FormulaType.DEFINITION:
            question = f"Explain the meaning and significance of {formula.name}: ${formula.latex}$. Provide an example of its application."
            exercise_type = ExerciseType.CONCEPTUAL
            difficulty = 2
        elif formula.type == FormulaType.THEOREM:
            question = f"State and apply {formula.name}: ${formula.latex}$. Show how this theorem can be used to solve a practical problem."
            exercise_type = ExerciseType.DERIVATION
            difficulty = 3
        else:
            question = f"Given the formula {formula.name}: ${formula.latex}$, solve a problem by substituting appropriate values and calculating the result."
            exercise_type = ExerciseType.SIMPLE_APPLICATION
            difficulty = 2
        
        return Exercise(
            id=generate_unique_id("exercise"),
            question=question,
            type=exercise_type,
            formula_ids=[formula.id],
            topic_ids=[formula.topic_id],
            difficulty=difficulty,
            solution="Apply the formula step by step, substituting given values and solving for the unknown."
        )
    
    def _select_formula_combinations(self, formulas: List[Formula], 
                                   topics: List[Topic], count: int) -> List[List[Formula]]:
        """Select combinations of formulas for comprehensive exercises"""
        
        combinations = []
        
        # Group formulas by topic
        topic_formulas = {}
        for formula in formulas:
            if formula.topic_id not in topic_formulas:
                topic_formulas[formula.topic_id] = []
            topic_formulas[formula.topic_id].append(formula)
        
        topic_ids = list(topic_formulas.keys())
        
        # Strategy 1: Combine formulas from different topics
        if len(topic_ids) >= 2:
            for i in range(min(count, len(topic_ids) - 1)):
                combination = []
                
                # Take 1-2 formulas from first topic
                if topic_ids[i] in topic_formulas:
                    combination.extend(topic_formulas[topic_ids[i]][:2])
                
                # Take 1-2 formulas from second topic
                if i + 1 < len(topic_ids) and topic_ids[i + 1] in topic_formulas:
                    combination.extend(topic_formulas[topic_ids[i + 1]][:2])
                
                if len(combination) >= 2:
                    combinations.append(combination[:3])  # Limit to 3 formulas
        
        # Strategy 2: Combine related formulas from same topic
        if len(combinations) < count:
            for topic_id, topic_formulas_list in topic_formulas.items():
                if len(topic_formulas_list) >= 2 and len(combinations) < count:
                    combinations.append(topic_formulas_list[:3])
        
        # Strategy 3: Random combinations if needed
        if len(combinations) < count and len(formulas) >= 2:
            remaining_count = count - len(combinations)
            for i in range(remaining_count):
                start_idx = i * 2
                if start_idx + 1 < len(formulas):
                    combination = formulas[start_idx:start_idx + 3]
                    combinations.append(combination)
        
        return combinations[:count]
    
    def _generate_comprehensive_exercise(self, formulas: List[Formula], 
                                       topics: List[Topic], exercise_num: int) -> Optional[Exercise]:
        """Generate a comprehensive exercise combining multiple formulas"""
        
        try:
            # Prepare context
            formula_info = [{"name": f.name, "latex": f.latex, "type": f.type.value} 
                           for f in formulas]
            
            topic_titles = []
            for formula in formulas:
                topic = next((t for t in topics if t.id == formula.topic_id), None)
                if topic and topic.title not in topic_titles:
                    topic_titles.append(topic.title)
            
            prompt = f"""
Create a comprehensive exercise that integrates the following formulas and concepts:

Formulas to combine:
{json.dumps(formula_info, indent=2)}

Related topics: {', '.join(topic_titles)}

Requirements:
1. Create a realistic scenario that requires using multiple formulas
2. The problem should have multiple steps
3. Students should need to understand relationships between concepts
4. Difficulty level should be 4-5 (challenging but solvable)
5. Provide a clear solution approach

Return your response in JSON format:
{{
    "question": "Comprehensive problem statement with specific scenario and values",
    "solution_approach": "Step-by-step solution methodology",
    "difficulty": 4,
    "key_concepts": ["concept1", "concept2"],
    "real_world_application": "Brief description of practical relevance"
}}

Make this a challenging but educational problem that demonstrates the interconnection of concepts.
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert educator creating challenging comprehensive exercises that integrate multiple mathematical concepts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1200
            )
            
            # Parse response
            json_match = re.search(r'\{.*\}', response.choices[0].message.content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                return Exercise(
                    id=generate_unique_id("comprehensive"),
                    question=data.get('question', ''),
                    type=ExerciseType.COMPREHENSIVE,
                    formula_ids=[f.id for f in formulas],
                    topic_ids=list(set(f.topic_id for f in formulas)),
                    solution=data.get('solution_approach', ''),
                    difficulty=data.get('difficulty', 4),
                    hints=data.get('key_concepts', [])
                )
                
        except Exception as e:
            logger.warning(f"Failed to generate comprehensive exercise {exercise_num}: {e}")
        
        return None
    
    def _generate_conceptual_exercise(self, topic: Topic) -> Optional[Exercise]:
        """Generate a conceptual understanding exercise for a topic"""
        
        try:
            prompt = f"""
Create a conceptual exercise for the topic: "{topic.title}"

Topic content: {topic.content[:300] if topic.content else ""}
Key terms: {', '.join(topic.keywords[:5]) if topic.keywords else ""}

Create an exercise that tests conceptual understanding rather than calculation. This could include:
- Explaining relationships between concepts
- Comparing and contrasting ideas
- Analyzing scenarios
- Interpreting results

Return your response in JSON format:
{{
    "question": "Conceptual question that tests understanding",
    "solution_approach": "How to approach this conceptual problem",
    "difficulty": 2,
    "learning_objective": "What students should learn from this exercise"
}}
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert educator creating conceptual exercises that test deep understanding."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            # Parse response
            json_match = re.search(r'\{.*\}', response.choices[0].message.content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                return Exercise(
                    id=generate_unique_id("conceptual"),
                    question=data.get('question', ''),
                    type=ExerciseType.CONCEPTUAL,
                    formula_ids=[],
                    topic_ids=[topic.id],
                    solution=data.get('solution_approach', ''),
                    difficulty=data.get('difficulty', 2)
                )
                
        except Exception as e:
            logger.warning(f"Failed to generate conceptual exercise for {topic.title}: {e}")
        
        return None
    
    def _load_exercise_templates(self) -> Dict[str, str]:
        """Load exercise templates for different types"""
        
        return {
            "calculation": "Given {formula_name}: ${formula}$, calculate the result when {variables}.",
            
            "application": "In a real-world scenario involving {context}, use {formula_name} to solve the following problem: {problem_statement}",
            
            "conceptual": "Explain the significance of {formula_name} and describe how it relates to {related_concepts}.",
            
            "derivation": "Starting from basic principles, derive {formula_name} and explain each step in the process.",
            
            "comparison": "Compare the results obtained using {formula1} and {formula2} for the given scenario: {scenario}",
            
            "comprehensive": "Solve the following multi-step problem that requires applying {formula_list}: {complex_scenario}"
        }
    
    def validate_exercise(self, exercise: Exercise) -> bool:
        """
        Validate an exercise for quality and completeness
        
        Args:
            exercise: Exercise to validate
            
        Returns:
            True if exercise is valid
        """
        # Check required fields
        if not exercise.question or len(exercise.question.strip()) < 10:
            return False
        
        if not exercise.formula_ids and not exercise.topic_ids:
            return False
        
        if exercise.difficulty < 1 or exercise.difficulty > 5:
            return False
        
        # Check question quality
        question_lower = exercise.question.lower()
        
        # Should contain some mathematical or educational content
        math_indicators = ['formula', 'calculate', 'solve', 'find', 'determine', 'explain', 'derive', 'apply']
        if not any(indicator in question_lower for indicator in math_indicators):
            return False
        
        return True
    
    def enhance_exercise_with_context(self, exercise: Exercise, 
                                    formulas: List[Formula], topics: List[Topic]) -> Exercise:
        """
        Enhance an exercise with additional context and information
        
        Args:
            exercise: Exercise to enhance
            formulas: Available formulas
            topics: Available topics
            
        Returns:
            Enhanced exercise
        """
        # Add related formulas information
        related_formulas = [f for f in formulas if f.id in exercise.formula_ids]
        
        # Add topic context
        related_topics = [t for t in topics if t.id in exercise.topic_ids]
        
        # Enhance hints with formula information
        if related_formulas and not exercise.hints:
            hints = []
            for formula in related_formulas:
                if formula.applications:
                    hints.append(f"Consider the applications of {formula.name}")
                if formula.derivation:
                    hints.append(f"Remember the derivation of {formula.name}")
            
            exercise.hints = hints[:3]  # Limit to 3 hints
        
        return exercise

