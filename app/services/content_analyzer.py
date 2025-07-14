"""
Content analysis service for processing extracted PDF content
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI
import tiktoken
import json

from app.models.schemas import (
    PDFContent, Topic, Formula, TopicType, FormulaType,
    AgentState
)

logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """Service for analyzing and structuring PDF content"""
    
    def __init__(self, openai_client: Optional[OpenAI] = None):
        self.client = openai_client or OpenAI()
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.max_tokens = 4000
        self.model = "gpt-3.5-turbo"
    
    def analyze_document_structure(self, pdf_content: PDFContent) -> List[Topic]:
        """
        Analyze document structure and identify main topics
        
        Args:
            pdf_content: Extracted PDF content
            
        Returns:
            List of identified topics
        """
        logger.info("Starting document structure analysis")
        
        # First, try to identify topics from text structure
        structural_topics = self._identify_structural_topics(pdf_content.text)
        
        # Then use AI to enhance and validate topics
        ai_topics = self._analyze_topics_with_ai(pdf_content.text, structural_topics)
        
        # Merge and deduplicate
        final_topics = self._merge_topics(structural_topics, ai_topics)
        
        logger.info(f"Identified {len(final_topics)} topics")
        return final_topics
    
    def extract_formulas(self, pdf_content: PDFContent, topics: List[Topic]) -> List[Formula]:
        """
        Extract and analyze formulas from the content
        
        Args:
            pdf_content: Extracted PDF content
            topics: Identified topics
            
        Returns:
            List of extracted formulas
        """
        logger.info("Starting formula extraction")
        
        # Extract formulas using pattern matching
        raw_formulas = self._extract_formulas_by_pattern(pdf_content.text)
        
        # Enhance formulas with AI analysis
        enhanced_formulas = self._enhance_formulas_with_ai(raw_formulas, pdf_content.text, topics)
        
        logger.info(f"Extracted {len(enhanced_formulas)} formulas")
        return enhanced_formulas
    
    def _identify_structural_topics(self, text: str) -> List[Topic]:
        """Identify topics based on text structure"""
        
        topics = []
        lines = text.split('\n')
        
        # Patterns for different heading levels
        patterns = [
            (r'^Chapter\s+(\d+)[:\.]?\s*(.+)$', 1, TopicType.CHAPTER),
            (r'^Section\s+(\d+)[:\.]?\s*(.+)$', 2, TopicType.SECTION),
            (r'^(\d+)\.\s+(.+)$', 2, TopicType.SECTION),
            (r'^(\d+)\.(\d+)\s+(.+)$', 3, TopicType.SUBSECTION),
            (r'^#{1,3}\s+(.+)$', 2, TopicType.SECTION),  # Markdown headers
        ]
        
        topic_id = 1
        current_page = 1
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            # Track page numbers
            if line.startswith('--- Page '):
                try:
                    page_match = re.search(r'--- Page (\d+) ---', line)
                    if page_match:
                        current_page = int(page_match.group(1))
                except (AttributeError, ValueError):
                    pass
                continue
            
            if not line or len(line) < 3:
                continue
            
            for pattern, level, topic_type in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        groups = match.groups()
                        if topic_type == TopicType.CHAPTER:
                            title = groups[1].strip() if len(groups) >= 2 else groups[0].strip()
                        elif len(groups) >= 3:  # Numbered subsection
                            title = groups[2].strip()
                        elif len(groups) >= 1:
                            title = groups[-1].strip()  # Last group
                        else:
                            title = match.group(0).strip()  # Fallback to full match
                        
                        if len(title) > 2 and not title.isdigit():
                            # Extract content for this topic (simplified)
                            content = self._extract_topic_content(lines, line_num, 50)
                            
                            topics.append(Topic(
                                id=f"topic_{topic_id}",
                                title=title,
                                type=topic_type,
                                level=level,
                                parent_id=None,  # Will be set later
                                content=content,
                                page_range=(current_page, current_page),
                                keywords=self._extract_keywords(content)
                            ))
                            topic_id += 1
                    except (AttributeError, IndexError) as e:
                        logger.warning(f"Error processing topic match: {e}")
                        continue
                    break
        
        # Set parent relationships
        self._set_parent_relationships(topics)
        
        return topics
    
    def _extract_topic_content(self, lines: List[str], start_line: int, max_lines: int = 50) -> str:
        """Extract content following a topic header"""
        
        content_lines = []
        
        for i in range(start_line + 1, min(start_line + max_lines, len(lines))):
            line = lines[i].strip()
            
            # Stop at next header
            if re.match(r'^(Chapter|Section|\d+\.|\#{1,3})', line, re.IGNORECASE):
                break
            
            if line and not line.startswith('--- Page'):
                content_lines.append(line)
        
        return '\n'.join(content_lines)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        
        # Simple keyword extraction based on frequency and patterns
        words = re.findall(r'\b[A-Za-z]{3,}\b', text.lower())
        
        # Filter common words
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'man', 'way', 'she', 'use', 'her', 'many', 'oil', 'sit', 'set', 'run', 'eat', 'far', 'sea', 'eye', 'ask', 'own', 'say', 'too', 'any', 'try', 'let', 'put', 'end', 'why', 'turn', 'here', 'show', 'every', 'good', 'me', 'give', 'our', 'under', 'name', 'very', 'through', 'just', 'form', 'sentence', 'great', 'think', 'where', 'help', 'much', 'before', 'move', 'right', 'too', 'means', 'old', 'any', 'same', 'tell', 'boy', 'follow', 'came', 'want', 'show', 'also', 'around', 'farm', 'three', 'small', 'set', 'put', 'end', 'does', 'another', 'well', 'large', 'must', 'big', 'even', 'such', 'because', 'turn', 'here', 'why', 'ask', 'went', 'men', 'read', 'need', 'land', 'different', 'home', 'us', 'move', 'try', 'kind', 'hand', 'picture', 'again', 'change', 'off', 'play', 'spell', 'air', 'away', 'animal', 'house', 'point', 'page', 'letter', 'mother', 'answer', 'found', 'study', 'still', 'learn', 'should', 'america', 'world'}
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Count frequency
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:10] if freq > 1]
    
    def _set_parent_relationships(self, topics: List[Topic]):
        """Set parent-child relationships between topics"""
        
        for i, topic in enumerate(topics):
            # Find parent (previous topic with lower level)
            for j in range(i - 1, -1, -1):
                if topics[j].level < topic.level:
                    topic.parent_id = topics[j].id
                    break
    
    def _analyze_topics_with_ai(self, text: str, structural_topics: List[Topic]) -> List[Topic]:
        """Use AI to analyze and enhance topic identification"""
        
        # Prepare text chunks to avoid token limits
        chunks = self._split_text_into_chunks(text, max_tokens=2000)
        ai_topics = []
        
        for chunk_idx, chunk in enumerate(chunks):
            try:
                prompt = self._create_topic_analysis_prompt(chunk, structural_topics)
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert at analyzing academic documents and identifying key topics and concepts."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                
                # Parse AI response
                ai_result = self._parse_topic_analysis_response(response.choices[0].message.content, chunk_idx)
                ai_topics.extend(ai_result)
                
            except Exception as e:
                logger.warning(f"AI topic analysis failed for chunk {chunk_idx}: {e}")
                continue
        
        return ai_topics
    
    def _create_topic_analysis_prompt(self, text: str, existing_topics: List[Topic]) -> str:
        """Create prompt for AI topic analysis"""
        
        existing_titles = [topic.title for topic in existing_topics]
        
        prompt = f"""
Analyze the following academic text and identify the main topics, concepts, and themes.

Text to analyze:
{text}

Existing topics found: {existing_titles}

Please identify:
1. Main topics and subtopics
2. Key concepts and definitions
3. Important themes

Return your analysis in JSON format with the following structure:
{{
    "topics": [
        {{
            "title": "Topic title",
            "type": "chapter|section|subsection|concept",
            "level": 1-3,
            "keywords": ["keyword1", "keyword2"],
            "description": "Brief description"
        }}
    ]
}}

Focus on academic and technical content. Avoid generic topics.
"""
        return prompt
    
    def _parse_topic_analysis_response(self, response: str, chunk_idx: int) -> List[Topic]:
        """Parse AI response for topic analysis"""
        
        topics = []
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                for idx, topic_data in enumerate(data.get('topics', [])):
                    topic_type = TopicType.CONCEPT
                    if topic_data.get('type') == 'chapter':
                        topic_type = TopicType.CHAPTER
                    elif topic_data.get('type') == 'section':
                        topic_type = TopicType.SECTION
                    elif topic_data.get('type') == 'subsection':
                        topic_type = TopicType.SUBSECTION
                    
                    topics.append(Topic(
                        id=f"ai_topic_{chunk_idx}_{idx}",
                        title=topic_data.get('title', ''),
                        type=topic_type,
                        level=topic_data.get('level', 2),
                        parent_id=None,
                        content=topic_data.get('description', ''),
                        page_range=(1, 1),  # Will be updated later
                        keywords=topic_data.get('keywords', [])
                    ))
                    
        except Exception as e:
            logger.warning(f"Failed to parse AI topic response: {e}")
        
        return topics
    
    def _merge_topics(self, structural_topics: List[Topic], ai_topics: List[Topic]) -> List[Topic]:
        """Merge structural and AI-identified topics"""
        
        # Start with structural topics as they have better positioning
        merged_topics = structural_topics.copy()
        
        # Add AI topics that don't overlap significantly
        for ai_topic in ai_topics:
            is_duplicate = False
            
            for existing_topic in merged_topics:
                # Check for similarity in titles
                if self._calculate_similarity(ai_topic.title.lower(), existing_topic.title.lower()) > 0.7:
                    is_duplicate = True
                    # Enhance existing topic with AI keywords
                    existing_topic.keywords.extend(ai_topic.keywords)
                    existing_topic.keywords = list(set(existing_topic.keywords))  # Remove duplicates
                    break
            
            if not is_duplicate and len(ai_topic.title) > 3:
                merged_topics.append(ai_topic)
        
        return merged_topics
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity"""
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _extract_formulas_by_pattern(self, text: str) -> List[Dict[str, Any]]:
        """Extract formulas using pattern matching"""
        
        formulas = []
        
        # Enhanced patterns for formula detection
        patterns = [
            # LaTeX style
            (r'\$\$([^$]+)\$\$', 'display_math'),
            (r'\$([^$\n]{3,})\$', 'inline_math'),
            (r'\\begin\{equation\}(.*?)\\end\{equation\}', 'equation'),
            (r'\\begin\{align\}(.*?)\\end\{align\}', 'align'),
            
            # Mathematical expressions
            (r'([A-Za-z_]\w*\s*=\s*[^,\.\n]{5,})', 'equation'),
            (r'([∫∑∏][^,\.\n]{3,})', 'integral_sum'),
            (r'([A-Za-z_]\w*\([^)]+\)\s*=\s*[^,\.\n]{3,})', 'function'),
            (r'(d[A-Za-z_]\w*/d[A-Za-z_]\w*[^,\.\n]*)', 'derivative'),
            (r'(∂[A-Za-z_]\w*/∂[A-Za-z_]\w*[^,\.\n]*)', 'partial_derivative'),
        ]
        
        formula_id = 1
        
        for pattern, formula_type in patterns:
            matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                formula_text = match.group(1) if len(match.groups()) > 0 else match.group(0)
                formula_text = formula_text.strip()
                
                # Filter out very short or invalid formulas
                if len(formula_text) < 3 or formula_text.isdigit():
                    continue
                
                # Get context around the formula
                start_pos = max(0, match.start() - 100)
                end_pos = min(len(text), match.end() + 100)
                context = text[start_pos:end_pos].replace('\n', ' ').strip()
                
                formulas.append({
                    'id': f"formula_{formula_id}",
                    'latex': formula_text,
                    'type': formula_type,
                    'context': context,
                    'position': match.start(),
                    'raw_match': match.group(0)
                })
                formula_id += 1
        
        # Remove duplicates
        unique_formulas = []
        seen_formulas = set()
        
        for formula in sorted(formulas, key=lambda x: x['position']):
            # Normalize formula for comparison
            normalized = re.sub(r'\s+', '', formula['latex'].lower())
            
            if normalized not in seen_formulas and len(normalized) > 2:
                seen_formulas.add(normalized)
                unique_formulas.append(formula)
        
        return unique_formulas
    
    def _enhance_formulas_with_ai(self, raw_formulas: List[Dict[str, Any]], 
                                 text: str, topics: List[Topic]) -> List[Formula]:
        """Enhance formulas with AI analysis"""
        
        enhanced_formulas = []
        
        # Process formulas in batches to avoid token limits
        batch_size = 5
        
        for i in range(0, len(raw_formulas), batch_size):
            batch = raw_formulas[i:i + batch_size]
            
            try:
                enhanced_batch = self._analyze_formula_batch_with_ai(batch, topics)
                enhanced_formulas.extend(enhanced_batch)
                
            except Exception as e:
                logger.warning(f"AI formula analysis failed for batch {i//batch_size}: {e}")
                
                # Fallback: create basic Formula objects
                for formula_data in batch:
                    enhanced_formulas.append(Formula(
                        id=formula_data['id'],
                        name=f"Formula {len(enhanced_formulas) + 1}",
                        latex=formula_data['latex'],
                        type=FormulaType.EQUATION,
                        topic_id=topics[0].id if topics else "unknown",
                        context=formula_data.get('context', ''),
                        page_number=1
                    ))
        
        return enhanced_formulas
    
    def _analyze_formula_batch_with_ai(self, formulas: List[Dict[str, Any]], 
                                     topics: List[Topic]) -> List[Formula]:
        """Analyze a batch of formulas with AI"""
        
        topic_info = [{"id": t.id, "title": t.title, "keywords": t.keywords} for t in topics]
        
        prompt = f"""
Analyze the following mathematical formulas and provide detailed information for each:

Formulas to analyze:
{json.dumps([{"id": f["id"], "formula": f["latex"], "context": f["context"][:200]} for f in formulas], indent=2)}

Available topics:
{json.dumps(topic_info, indent=2)}

For each formula, provide:
1. A descriptive name
2. The type (equation, theorem, definition, property)
3. Which topic it belongs to (use topic ID)
4. Brief explanation of what it represents
5. Potential applications

Return your analysis in JSON format:
{{
    "formulas": [
        {{
            "id": "formula_id",
            "name": "Descriptive name",
            "type": "equation|theorem|definition|property",
            "topic_id": "topic_id",
            "explanation": "What this formula represents",
            "applications": ["application1", "application2"]
        }}
    ]
}}
"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert mathematician and educator analyzing mathematical formulas."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        # Parse response and create Formula objects
        enhanced_formulas = []
        
        try:
            json_match = re.search(r'\{.*\}', response.choices[0].message.content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                for formula_data in data.get('formulas', []):
                    # Find original formula
                    original = next((f for f in formulas if f['id'] == formula_data['id']), None)
                    if not original:
                        continue
                    
                    # Map type
                    formula_type = FormulaType.EQUATION
                    type_str = formula_data.get('type', 'equation').lower()
                    if type_str == 'theorem':
                        formula_type = FormulaType.THEOREM
                    elif type_str == 'definition':
                        formula_type = FormulaType.DEFINITION
                    elif type_str == 'property':
                        formula_type = FormulaType.PROPERTY
                    
                    enhanced_formulas.append(Formula(
                        id=formula_data['id'],
                        name=formula_data.get('name', f"Formula {len(enhanced_formulas) + 1}"),
                        latex=original['latex'],
                        type=formula_type,
                        topic_id=formula_data.get('topic_id', topics[0].id if topics else "unknown"),
                        derivation=formula_data.get('explanation', ''),
                        applications=formula_data.get('applications', []),
                        context=original.get('context', ''),
                        page_number=1  # Will be updated later
                    ))
                    
        except Exception as e:
            logger.warning(f"Failed to parse AI formula response: {e}")
        
        return enhanced_formulas
    
    def _split_text_into_chunks(self, text: str, max_tokens: int = 2000) -> List[str]:
        """Split text into chunks that fit within token limits"""
        
        # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
        estimated_tokens = len(text) // 4
        
        if estimated_tokens <= max_tokens:
            return [text]
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # Check if adding this paragraph would exceed limit
            test_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            
            if len(test_chunk) // 4 > max_tokens:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = paragraph
                else:
                    # Paragraph is too long, split by sentences
                    sentences = paragraph.split('. ')
                    for sentence in sentences:
                        if len(current_chunk + sentence) // 4 > max_tokens:
                            if current_chunk:
                                chunks.append(current_chunk)
                                current_chunk = sentence
                            else:
                                chunks.append(sentence)  # Single sentence is too long
                        else:
                            current_chunk += ". " + sentence if current_chunk else sentence
            else:
                current_chunk = test_chunk
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

