#!/usr/bin/env python3
"""
Simple test script to verify the fixes in the Notes Taking Agent
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.schemas import PDFContent, Topic, Formula, AgentState, TopicType, FormulaType
from app.services.content_analyzer import ContentAnalyzer
from app.utils.helpers import generate_unique_id, get_timestamp

def test_formula_model():
    """Test Formula model and attribute access"""
    print("🧪 Testing Formula model...")
    
    formula = Formula(
        id="test_formula_1",
        name="Test Formula",
        latex="E = mc^2",
        type=FormulaType.EQUATION,
        topic_id="topic_1",
        derivation="Energy equals mass times speed of light squared",
        page_number=1,
        context="This is Einstein's famous equation"
    )
    
    # Test accessing derivation (not explanation)
    explanation = getattr(formula, 'derivation', '')
    print(f"✅ Formula derivation access: {explanation[:50]}...")
    
    return True

def test_content_analyzer():
    """Test ContentAnalyzer with sample text"""
    print("🧪 Testing ContentAnalyzer...")
    
    # Create sample PDF content
    sample_text = """
Chapter 1: Introduction to Physics
This chapter covers basic concepts.

Section 1.1: Classical Mechanics
Newton's laws of motion are fundamental.

1.2 Energy and Work
The formula E = mc^2 is important.

2. Quantum Mechanics
Quantum theory explains atomic behavior.
"""
    
    pdf_content = PDFContent(
        text=sample_text,
        pages=1,
        metadata={},
        images=[],
        tables=[]
    )
    
    try:
        analyzer = ContentAnalyzer()
        topics = analyzer._identify_structural_topics(sample_text)
        print(f"✅ Found {len(topics)} topics without regex errors")
        
        for topic in topics:
            print(f"   - {topic.title}")
        
        return True
    except Exception as e:
        print(f"❌ ContentAnalyzer test failed: {e}")
        return False

def test_agent_state():
    """Test AgentState with empty topics/formulas"""
    print("🧪 Testing AgentState handling...")
    
    state = AgentState(
        current_step="testing",
        metadata={"filename": "test.pdf"}
    )
    
    # Test empty state handling
    if not state.topics and not state.formulas:
        print("✅ Empty state handling works correctly")
        return True
    else:
        print("❌ State initialization issue")
        return False

def main():
    """Run all tests"""
    print("🚀 Notes Taking Agent - Fix Verification Tests")
    print("=" * 50)
    
    tests = [
        test_formula_model,
        test_content_analyzer,
        test_agent_state
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Fixes appear to be working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the fixes.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

