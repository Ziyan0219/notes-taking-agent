#!/usr/bin/env python3
"""
Startup script for Notes Taking Agent
"""

import os
import sys
import subprocess
from pathlib import Path
import uvicorn

def check_environment():
    """Check environment setup"""
    print("🔧 Checking environment...")
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found")
        print("📝 Creating .env from template...")
        
        template_file = Path(".env.template")
        if template_file.exists():
            # Copy template to .env
            with open(template_file, 'r') as f:
                template_content = f.read()
            
            with open(env_file, 'w') as f:
                f.write(template_content)
            
            print("✅ .env file created from template")
            print("⚠️  Please edit .env file and add your OpenAI API key")
            return False
        else:
            print("❌ .env.template not found")
            return False
    
    # Check OpenAI API key
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env file")
        print("📝 Please add your OpenAI API key to .env file")
        return False
    
    print("✅ Environment setup complete")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = [
        "uploads",
        "generated_notes",
        "static",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ {directory}/")
    
    return True

def run_basic_tests():
    """Run basic functionality tests"""
    print("🧪 Running basic tests...")
    
    try:
        # Test imports
        from app.main import app
        from app.models.schemas import Topic
        from app.services.pdf_parser import PDFParser
        
        print("✅ Basic imports successful")
        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting Notes Taking Agent server...")
    print("=" * 50)
    
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    print(f"🌐 Server will start at: http://{host}:{port}")
    print("📚 Upload PDF files to generate structured notes")
    print("🔧 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=debug,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        return False
    
    return True

def main():
    """Main startup function"""
    print("🚀 Notes Taking Agent - Startup")
    print("=" * 50)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Check and install dependencies
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found")
        return 1
    
    print("📦 Checking dependencies...")
    try:
        import fastapi
        import uvicorn
        print("✅ Core dependencies available")
    except ImportError:
        print("⚠️  Installing core dependencies...")
        if not install_dependencies():
            return 1
    
    # Create directories
    if not create_directories():
        return 1
    
    # Check environment
    if not check_environment():
        print("\n⚠️  Environment setup incomplete")
        print("Please configure your .env file and run again")
        return 1
    
    # Run basic tests
    if not run_basic_tests():
        print("\n❌ Basic tests failed")
        print("Please check your installation and try again")
        return 1
    
    # Start server
    start_server()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

