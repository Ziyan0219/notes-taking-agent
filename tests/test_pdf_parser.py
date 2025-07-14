"""
Tests for PDF parser service
"""

import pytest
from pathlib import Path
import tempfile
import os

from app.services.pdf_parser import PDFParser
from app.models.schemas import PDFContent


class TestPDFParser:
    """Test cases for PDF parser"""
    
    def setup_method(self):
        """Setup test environment"""
        self.parser = PDFParser()
    
    def test_parser_initialization(self):
        """Test parser initialization"""
        assert self.parser is not None
        assert self.parser.supported_formats == ['.pdf']
    
    def test_extract_formulas_basic(self):
        """Test basic formula extraction"""
        text = """
        This is a test document with some formulas.
        
        The quadratic formula is: $x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$
        
        Another equation: $E = mc^2$
        
        And a display formula:
        $$F = ma$$
        """
        
        formulas = self.parser.extract_formulas(text)
        
        assert len(formulas) >= 2
        assert any('quadratic' in f['latex'].lower() or 'frac' in f['latex'] for f in formulas)
        assert any('E = mc' in f['latex'] for f in formulas)
    
    def test_identify_topics_basic(self):
        """Test basic topic identification"""
        text = """
        Chapter 1: Introduction to Physics
        
        This chapter covers basic concepts.
        
        Section 1.1: Motion
        
        Motion is the change in position.
        
        1.2 Forces
        
        Forces cause acceleration.
        """
        
        topics = self.parser.identify_topics(text)
        
        assert len(topics) >= 2
        topic_titles = [t['title'] for t in topics]
        assert any('Introduction to Physics' in title for title in topic_titles)
        assert any('Motion' in title for title in topic_titles)
    
    def test_extract_formulas_edge_cases(self):
        """Test formula extraction edge cases"""
        # Empty text
        formulas = self.parser.extract_formulas("")
        assert len(formulas) == 0
        
        # Text without formulas
        text = "This is just plain text without any mathematical content."
        formulas = self.parser.extract_formulas(text)
        assert len(formulas) == 0
        
        # Malformed LaTeX
        text = "This has incomplete LaTeX: $x = incomplete"
        formulas = self.parser.extract_formulas(text)
        # Should handle gracefully
        assert isinstance(formulas, list)
    
    def test_identify_topics_edge_cases(self):
        """Test topic identification edge cases"""
        # Empty text
        topics = self.parser.identify_topics("")
        assert len(topics) == 0
        
        # Text without clear structure
        text = "This is just a paragraph of text without any clear headings or structure."
        topics = self.parser.identify_topics(text)
        # Should return empty or minimal results
        assert isinstance(topics, list)
    
    def test_formula_deduplication(self):
        """Test that duplicate formulas are removed"""
        text = """
        The same formula appears twice:
        $E = mc^2$
        
        And again:
        $E = mc^2$
        """
        
        formulas = self.parser.extract_formulas(text)
        
        # Should deduplicate
        formula_texts = [f['latex'] for f in formulas]
        assert len(set(formula_texts)) == len(formula_texts)
    
    def test_formula_context_extraction(self):
        """Test that formula context is extracted"""
        text = """
        Einstein's famous equation relates energy and mass.
        The equation is: $E = mc^2$
        This shows the equivalence of mass and energy.
        """
        
        formulas = self.parser.extract_formulas(text)
        
        assert len(formulas) >= 1
        formula = formulas[0]
        assert 'context' in formula
        assert len(formula['context']) > 0
        assert 'Einstein' in formula['context'] or 'energy' in formula['context']
    
    def test_topic_hierarchy(self):
        """Test topic hierarchy detection"""
        text = """
        Chapter 1: Mechanics
        
        Section 1.1: Kinematics
        
        1.1.1 Position and Displacement
        
        Section 1.2: Dynamics
        """
        
        topics = self.parser.identify_topics(text)
        
        # Should identify different levels
        levels = [t.get('level', 1) for t in topics]
        assert min(levels) < max(levels)  # Should have different levels
    
    @pytest.mark.parametrize("formula_text,expected_type", [
        ("$x = 5$", "expression"),
        ("$$\\int_0^1 x dx$$", "latex"),
        ("$\\sum_{i=1}^n i$", "latex"),
        ("F = ma", "expression")
    ])
    def test_formula_type_detection(self, formula_text, expected_type):
        """Test formula type detection"""
        formulas = self.parser.extract_formulas(formula_text)
        
        if formulas:  # If formula was detected
            formula = formulas[0]
            assert formula['type'] == expected_type
    
    def test_large_text_handling(self):
        """Test handling of large text documents"""
        # Create a large text with many formulas
        large_text = ""
        for i in range(100):
            large_text += f"Section {i}: Formula $x_{i} = {i}$\n"
        
        formulas = self.parser.extract_formulas(large_text)
        topics = self.parser.identify_topics(large_text)
        
        # Should handle without errors
        assert isinstance(formulas, list)
        assert isinstance(topics, list)
        assert len(formulas) > 0
        assert len(topics) > 0


class TestPDFParserIntegration:
    """Integration tests for PDF parser"""
    
    def setup_method(self):
        """Setup test environment"""
        self.parser = PDFParser()
    
    def test_nonexistent_file(self):
        """Test handling of nonexistent files"""
        with pytest.raises(FileNotFoundError):
            self.parser.parse_pdf(Path("nonexistent.pdf"))
    
    def test_unsupported_format(self):
        """Test handling of unsupported file formats"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = Path(tmp.name)
        
        try:
            with pytest.raises(ValueError):
                self.parser.parse_pdf(tmp_path)
        finally:
            os.unlink(tmp_path)
    
    def test_get_pdf_info_nonexistent(self):
        """Test PDF info for nonexistent file"""
        with pytest.raises(Exception):
            self.parser.get_pdf_info(Path("nonexistent.pdf"))


if __name__ == "__main__":
    pytest.main([__file__])

