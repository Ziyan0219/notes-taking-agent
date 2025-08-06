#!/usr/bin/env python3
"""
启动Web笔记生成器
"""

import os
import sys
from pathlib import Path
import uvicorn

def check_dependencies():
    """检查依赖"""
    print("检查依赖...")
    
    try:
        import fastapi
        import uvicorn
        print("✓ FastAPI 可用")
    except ImportError:
        print("✗ 缺少 FastAPI，正在安装...")
        os.system(f"{sys.executable} -m pip install fastapi uvicorn python-multipart jinja2")
    
    try:
        import openai
        print("✓ OpenAI 可用 (完整功能)")
        ai_available = True
    except ImportError:
        print("⚠ OpenAI 未安装 (将使用演示模式)")
        ai_available = False
    
    try:
        import fitz
        print("✓ PyMuPDF 可用 (PDF处理)")
        pdf_available = True
    except ImportError:
        print("⚠ PyMuPDF 未安装 (将使用演示模式)")
        pdf_available = False
    
    return ai_available, pdf_available

def create_directories():
    """创建必要目录"""
    dirs = ["uploads", "generated_notes", "static_web", "templates_web"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✓ 目录: {dir_name}")

def main():
    print("=" * 50)
    print("🚀 启动实战笔记生成器 Web版")
    print("=" * 50)
    
    # 检查依赖
    ai_available, pdf_available = check_dependencies()
    
    # 创建目录
    create_directories()
    
    print("\n📊 功能状态:")
    print(f"  AI处理: {'✓ 可用' if ai_available else '✗ 演示模式'}")
    print(f"  PDF处理: {'✓ 可用' if pdf_available else '✗ 演示模式'}")
    
    print("\n🌐 启动Web服务器...")
    print("访问地址: http://localhost:8080")
    print("按 Ctrl+C 停止服务")
    print("=" * 50)
    
    try:
        # 启动服务器
        uvicorn.run(
            "web_app:app",
            host="0.0.0.0",
            port=8080,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n👋 服务器已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        print("\n可能的解决方案:")
        print("1. 确保端口8080未被占用")
        print("2. 检查防火墙设置")
        print("3. 尝试不同端口: uvicorn web_app:app --port 8081")

if __name__ == "__main__":
    main()