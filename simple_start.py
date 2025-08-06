#!/usr/bin/env python3
"""
简单启动脚本 - 实战笔记生成器
"""

import os
import sys
from pathlib import Path
import subprocess

def print_banner():
    print("=" * 60)
    print("实战笔记生成器 - 快速启动")
    print("=" * 60)
    print("专注本科难度，以做题为导向的AI笔记系统")
    print()

def check_files():
    """检查文件是否存在"""
    files = {
        "complete_notes_system.py": "新系统主程序",
        "practical_notes_formatter.py": "笔记格式化器", 
        "app/main.py": "原Web系统",
        "requirements.txt": "依赖列表"
    }
    
    print("文件检查:")
    all_exists = True
    
    for file_path, desc in files.items():
        exists = Path(file_path).exists()
        status = "OK" if exists else "缺失"
        print(f"  {status}: {file_path} ({desc})")
        if not exists:
            all_exists = False
    
    return all_exists

def show_options():
    """显示使用选项"""
    print("\n使用方法:")
    print()
    
    print("1. 快速测试 (推荐，无需API Key)")
    print("   python complete_notes_system.py")
    print()
    
    print("2. AI处理PDF (需要OpenAI API Key)")
    print("   python complete_notes_system.py file.pdf --api-key YOUR_KEY")
    print()
    
    print("3. Web界面 (原系统)")
    print("   python app/main.py")
    print("   然后访问: http://localhost:8000")
    print()

def run_test():
    """运行快速测试"""
    print("正在运行快速测试...")
    
    try:
        result = subprocess.run([
            sys.executable, "complete_notes_system.py"
        ], check=True, capture_output=True, text=True)
        
        print("测试成功!")
        print("输出目录: test_output/")
        print("主要文件:")
        print("  - test_notes.md")  
        print("  - test_notes.html")
        print("  - test_notes.json")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"测试失败: {e}")
        return False
    except Exception as e:
        print(f"运行错误: {e}")
        return False

def main():
    print_banner()
    
    # 检查文件
    if not check_files():
        print("\n警告: 某些文件缺失，功能可能受限")
    
    # 显示选项
    show_options()
    
    # 询问是否运行测试
    choice = input("是否运行快速测试? (y/n): ").strip().lower()
    
    if choice in ['y', 'yes', '是']:
        print()
        success = run_test()
        if success:
            print("\n查看生成的笔记文件了解效果!")
    
    print("\n" + "=" * 60)
    print("使用说明:")
    print("1. 快速测试: python complete_notes_system.py")
    print("2. 查看新README: README_NEW.md")
    print("3. 安装依赖: pip install -r requirements_new.txt")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户取消操作")
    except Exception as e:
        print(f"程序错误: {e}")