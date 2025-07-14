#!/usr/bin/env python3
"""
Test runner script for Notes Taking Agent
"""

import sys
import subprocess
import os
from pathlib import Path

def run_tests():
    """Run all tests"""
    print("🧪 Running Notes Taking Agent Tests")
    print("=" * 50)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Check if pytest is available
    try:
        import pytest
        print("✅ pytest is available")
    except ImportError:
        print("❌ pytest not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest"], check=True)
        import pytest
    
    # Run tests
    test_files = [
        "tests/test_pdf_parser.py",
        "tests/test_content_analyzer.py"
    ]
    
    all_passed = True
    
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"\n🔍 Running {test_file}...")
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test_file, "-v", "--tb=short"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {test_file} passed")
            else:
                print(f"❌ {test_file} failed")
                print(result.stdout)
                print(result.stderr)
                all_passed = False
        else:
            print(f"⚠️  {test_file} not found")
    
    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1

def check_dependencies():
    """Check if all dependencies are installed"""
    print("📦 Checking dependencies...")
    
    required_packages = [
        "fastapi", "uvicorn", "python-multipart",
        "langgraph", "langchain", "openai",
        "PyPDF2", "pdfplumber", "python-dotenv",
        "jinja2", "aiofiles"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed")
    return True

def test_basic_imports():
    """Test basic imports"""
    print("\n🔧 Testing basic imports...")
    
    try:
        from app.models.schemas import Topic, Formula, Exercise
        print("✅ Models import successful")
    except Exception as e:
        print(f"❌ Models import failed: {e}")
        return False
    
    try:
        from app.services.pdf_parser import PDFParser
        print("✅ PDF parser import successful")
    except Exception as e:
        print(f"❌ PDF parser import failed: {e}")
        return False
    
    try:
        from app.services.content_analyzer import ContentAnalyzer
        print("✅ Content analyzer import successful")
    except Exception as e:
        print(f"❌ Content analyzer import failed: {e}")
        return False
    
    try:
        from app.agents.notes_agent import NotesAgent
        print("✅ Notes agent import successful")
    except Exception as e:
        print(f"❌ Notes agent import failed: {e}")
        return False
    
    return True

def main():
    """Main test runner"""
    print("🚀 Notes Taking Agent - Test Suite")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Test imports
    if not test_basic_imports():
        return 1
    
    # Run tests
    return run_tests()

if __name__ == "__main__":
    sys.exit(main())

