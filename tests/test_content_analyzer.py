"""
Tests for content analyzer service
"""

import pytest
from unittest.mock import Mock, patch
import json

from app.services.content_analyzer import ContentAnalyzer
from app.models.schemas import PDFContent, Topic, Formula, TopicType, FormulaType


class TestContentAnalyzer:
    """Test cases for content analyzer"""
    
    def setup_method(self):
        """Setup test environment"""
        # Mock OpenAI client to avoid API calls in tests
        mock_client = Mock()
        self.analyzer = ContentAnalyzer(mock_client)
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization"""
        assert self.analyzer is not None
        assert self.analyzer.max_tokens == 4000
        assert self.analyzer.model == "gpt-3.5-turbo"
    
    def test_split_text_into_chunks(self):
        """Test text chunking functionality"""
        # Short text should remain as one chunk
        short_text = "This is a short text."
        chunks = self.analyzer._split_text_into_chunks(short_text, max_tokens=1000)
        assert len(chunks) == 1
        assert chunks[0] == short_text
        
        # Long text should be split
        long_text = "This is a sentence. " * 1000  # Very long text
        chunks = self.analyzer._split_text_into_chunks(long_text, max_tokens=100)
        assert len(chunks) > 1
        
        # Each chunk should be within reasonable size
        for chunk in chunks:
            estimated_tokens = len(chunk) // 4
            assert estimated_tokens <= 150  # Some buffer for the limit
    
    def test_calculate_similarity(self):
        """Test text similarity calculation"""
        # Identical texts
        similarity = self.analyzer._calculate_similarity("hello world", "hello world")
        assert similarity == 1.0
        
        # Completely different texts
        similarity = self.analyzer._calculate_similarity("hello world", "foo bar")
        assert similarity == 0.0
        
        # Partially similar texts
        similarity = self.analyzer._calculate_similarity("hello world", "hello universe")
        assert 0.0 < similarity < 1.0
        
        # Empty texts
        similarity = self.analyzer._calculate_similarity("", "")
        assert similarity == 0.0
    
    def test_extract_keywords(self):
        """Test keyword extraction"""
        text = """
        This document discusses quantum mechanics and wave functions.
        The Schrödinger equation is fundamental to quantum mechanics.
        Wave functions describe the quantum state of particles.
        Quantum mechanics quantum mechanics quantum mechanics.
        """
        
        keywords = self.analyzer._extract_keywords(text)
        
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        
        # Should include repeated important terms
        keyword_text = " ".join(keywords).lower()
        assert "quantum" in keyword_text
        assert "mechanics" in keyword_text
    
    def test_set_parent_relationships(self):
        """Test parent-child relationship setting"""
        topics = [
            Topic(
                id="topic_1", title="Chapter 1", type=TopicType.CHAPTER, level=1,
                parent_id=None, content="", page_range=(1, 1), keywords=[]
            ),
            Topic(
                id="topic_2", title="Section 1.1", type=TopicType.SECTION, level=2,
                parent_id=None, content="", page_range=(1, 1), keywords=[]
            ),
            Topic(
                id="topic_3", title="Subsection 1.1.1", type=TopicType.SUBSECTION, level=3,
                parent_id=None, content="", page_range=(1, 1), keywords=[]
            ),
            Topic(
                id="topic_4", title="Section 1.2", type=TopicType.SECTION, level=2,
                parent_id=None, content="", page_range=(1, 1), keywords=[]
            )
        ]
        
        self.analyzer._set_parent_relationships(topics)
        
        # Check parent relationships
        assert topics[0].parent_id is None  # Chapter has no parent
        assert topics[1].parent_id == "topic_1"  # Section 1.1 -> Chapter 1
        assert topics[2].parent_id == "topic_2"  # Subsection 1.1.1 -> Section 1.1
        assert topics[3].parent_id == "topic_1"  # Section 1.2 -> Chapter 1
    
    def test_extract_topic_content(self):
        """Test topic content extraction"""
        lines = [
            "Chapter 1: Introduction",
            "This chapter introduces basic concepts.",
            "We will cover fundamental principles.",
            "",
            "Chapter 2: Advanced Topics",
            "This chapter covers advanced material."
        ]
        
        content = self.analyzer._extract_topic_content(lines, 0, max_lines=3)
        
        assert "This chapter introduces" in content
        assert "We will cover" in content
        assert "Chapter 2" not in content  # Should stop at next header
    
    def test_identify_structural_topics(self):
        """Test structural topic identification"""
        text = """
        Chapter 1: Mechanics
        
        This chapter covers classical mechanics.
        
        Section 1.1: Kinematics
        
        Kinematics deals with motion.
        
        1.2 Dynamics
        
        Dynamics involves forces.
        
        # Modern Physics
        
        This covers quantum mechanics.
        """
        
        topics = self.analyzer._identify_structural_topics(text)
        
        assert len(topics) >= 3
        
        # Check that different types are identified
        topic_titles = [t.title for t in topics]
        assert any("Mechanics" in title for title in topic_titles)
        assert any("Kinematics" in title for title in topic_titles)
        assert any("Dynamics" in title for title in topic_titles)
        
        # Check levels
        levels = [t.level for t in topics]
        assert 1 in levels  # Chapter level
        assert 2 in levels  # Section level
    
    @patch('app.services.content_analyzer.ContentAnalyzer._analyze_topics_with_ai')
    def test_analyze_document_structure(self, mock_ai_analysis):
        """Test document structure analysis"""
        # Mock AI response
        mock_ai_analysis.return_value = []
        
        pdf_content = PDFContent(
            text="""
            Chapter 1: Introduction
            This is the introduction.
            
            Section 1.1: Overview
            This is an overview.
            """,
            pages=1,
            metadata={},
            images=[],
            tables=[]
        )
        
        topics = self.analyzer.analyze_document_structure(pdf_content)
        
        assert isinstance(topics, list)
        assert len(topics) >= 1
        
        # Verify mock was called
        mock_ai_analysis.assert_called_once()
    
    def test_extract_formulas_by_pattern(self):
        """Test pattern-based formula extraction"""
        text = """
        The quadratic formula is: $x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$
        
        Einstein's equation: $E = mc^2$
        
        A display equation:
        $$F = ma$$
        
        An integral: $\\int_0^1 x dx$
        
        A simple equation: v = at
        """
        
        formulas = self.analyzer._extract_formulas_by_pattern(text)
        
        assert len(formulas) >= 3
        
        # Check that different types are detected
        formula_texts = [f['latex'] for f in formulas]
        assert any('frac' in latex for latex in formula_texts)  # Quadratic formula
        assert any('mc^2' in latex for latex in formula_texts)  # Einstein
        assert any('ma' in latex for latex in formula_texts)    # F = ma
    
    def test_merge_topics(self):
        """Test topic merging functionality"""
        structural_topics = [
            Topic(
                id="struct_1", title="Quantum Mechanics", type=TopicType.CHAPTER, level=1,
                parent_id=None, content="", page_range=(1, 1), keywords=["quantum"]
            )
        ]
        
        ai_topics = [
            Topic(
                id="ai_1", title="Quantum Physics", type=TopicType.CONCEPT, level=2,
                parent_id=None, content="", page_range=(1, 1), keywords=["physics", "quantum"]
            ),
            Topic(
                id="ai_2", title="Wave Functions", type=TopicType.CONCEPT, level=2,
                parent_id=None, content="", page_range=(1, 1), keywords=["wave", "function"]
            )
        ]
        
        merged = self.analyzer._merge_topics(structural_topics, ai_topics)
        
        assert len(merged) >= 2
        
        # Should include structural topics
        titles = [t.title for t in merged]
        assert "Quantum Mechanics" in titles
        
        # Should merge similar topics and enhance keywords
        quantum_topic = next(t for t in merged if "Quantum" in t.title)
        assert len(quantum_topic.keywords) > 1
    
    def test_parse_topic_analysis_response(self):
        """Test parsing of AI topic analysis response"""
        response = '''
        Here are the identified topics:
        
        {
            "topics": [
                {
                    "title": "Classical Mechanics",
                    "type": "chapter",
                    "level": 1,
                    "keywords": ["mechanics", "classical", "motion"],
                    "description": "Study of motion and forces"
                },
                {
                    "title": "Newton's Laws",
                    "type": "section",
                    "level": 2,
                    "keywords": ["newton", "laws", "force"],
                    "description": "Three fundamental laws of motion"
                }
            ]
        }
        '''
        
        topics = self.analyzer._parse_topic_analysis_response(response, chunk_idx=0)
        
        assert len(topics) == 2
        assert topics[0].title == "Classical Mechanics"
        assert topics[0].type == TopicType.CHAPTER
        assert topics[1].title == "Newton's Laws"
        assert topics[1].type == TopicType.SECTION
        assert "mechanics" in topics[0].keywords
    
    def test_parse_topic_analysis_response_invalid_json(self):
        """Test parsing with invalid JSON"""
        response = "This is not valid JSON content"
        
        topics = self.analyzer._parse_topic_analysis_response(response, chunk_idx=0)
        
        assert isinstance(topics, list)
        assert len(topics) == 0  # Should handle gracefully


class TestContentAnalyzerIntegration:
    """Integration tests for content analyzer"""
    
    def setup_method(self):
        """Setup test environment"""
        # Use real analyzer but mock expensive operations
        self.analyzer = ContentAnalyzer()
    
    @patch('openai.OpenAI')
    def test_full_analysis_workflow(self, mock_openai):
        """Test complete analysis workflow"""
        # Mock OpenAI responses
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"topics": []}'
        mock_client.chat.completions.create.return_value = mock_response
        
        analyzer = ContentAnalyzer(mock_client)
        
        pdf_content = PDFContent(
            text="""
            Chapter 1: Physics Fundamentals
            
            This chapter introduces basic physics concepts.
            
            The fundamental equation is: $F = ma$
            
            Section 1.1: Motion
            
            Motion is described by: $v = at$
            """,
            pages=1,
            metadata={},
            images=[],
            tables=[]
        )
        
        # Test document structure analysis
        topics = analyzer.analyze_document_structure(pdf_content)
        assert isinstance(topics, list)
        
        # Test formula extraction
        formulas = analyzer.extract_formulas(pdf_content, topics)
        assert isinstance(formulas, list)


if __name__ == "__main__":
    pytest.main([__file__])

