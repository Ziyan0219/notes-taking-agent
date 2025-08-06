#!/usr/bin/env python3
"""
快速启动脚本 - 实战笔记生成器
帮助用户快速了解和使用系统
"""

import os
import sys
from pathlib import Path
import subprocess

def print_banner():
    """显示欢迎信息"""
    print("=" * 60)
    print("🎯 实战笔记生成器 - 快速启动")
    print("=" * 60)
    print("专注本科难度，以做题为导向的AI笔记系统")
    print()

def check_dependencies():
    """检查依赖是否安装"""
    print("📦 检查依赖...")
    
    required_basic = ['json', 're', 'pathlib']  # 内置模块
    missing_basic = []
    
    for module in required_basic:
        try:
            __import__(module)
        except ImportError:
            missing_basic.append(module)
    
    if missing_basic:
        print(f"❌ 缺少基础模块: {missing_basic}")
        return False
    
    print("✅ 基础模块检查通过")
    
    # 检查可选依赖
    optional_deps = {
        'openai': '完整AI功能',
        'fitz': 'PDF处理 (PyMuPDF)',
        'dotenv': '环境变量支持'
    }
    
    available_features = []
    missing_features = []
    
    for module, desc in optional_deps.items():
        try:
            if module == 'fitz':
                import fitz
            else:
                __import__(module)
            available_features.append(f"✅ {desc}")
        except ImportError:
            missing_features.append(f"❌ {desc} (pip install {module if module != 'fitz' else 'PyMuPDF'})")
    
    print("\n可用功能:")
    for feature in available_features:
        print(f"  {feature}")
    
    if missing_features:
        print("\n缺少功能 (可选):")
        for feature in missing_features:
            print(f"  {feature}")
    
    return True

def show_usage_options():
    """显示使用选项"""
    print("\n🚀 使用选项:")
    print()
    
    print("1. 📝 快速测试 (无需API Key)")
    print("   python complete_notes_system.py")
    print("   → 生成示例笔记，查看效果")
    print()
    
    print("2. 🤖 完整AI功能 (需要API Key)")
    print("   python complete_notes_system.py your_file.pdf --api-key YOUR_KEY")
    print("   → 处理真实PDF文件")
    print()
    
    print("3. 🌐 Web界面 (原系统)")
    print("   python app/main.py")
    print("   → 启动Web界面: http://localhost:8000")
    print()

def interactive_setup():
    """交互式设置"""
    print("🔧 交互式设置")
    print()
    
    choice = input("选择运行模式 (1-快速测试 / 2-AI处理 / 3-Web界面): ").strip()
    
    if choice == "1":
        print("\n🎯 运行快速测试...")
        try:
            import complete_notes_system
            print("✅ 模块加载成功")
            print("运行: python complete_notes_system.py")
            return "test"
        except ImportError as e:
            print(f"❌ 模块加载失败: {e}")
            return None
    
    elif choice == "2":
        api_key = input("输入OpenAI API Key (或按Enter跳过): ").strip()
        if not api_key:
            print("⚠️ 没有API Key，将使用测试模式")
            return "test"
        
        pdf_file = input("输入PDF文件路径 (或按Enter使用默认): ").strip()
        if not pdf_file:
            print("⚠️ 没有指定文件，将使用测试模式")
            return "test"
        
        if not Path(pdf_file).exists():
            print(f"❌ 文件不存在: {pdf_file}")
            return None
        
        print(f"\n🤖 处理文件: {pdf_file}")
        print(f"🔑 使用API Key: {api_key[:10]}...")
        return ("process", pdf_file, api_key)
    
    elif choice == "3":
        print("\n🌐 启动Web界面...")
        try:
            # 检查main.py是否存在
            main_path = Path("app/main.py")
            if not main_path.exists():
                print("❌ 未找到 app/main.py")
                return None
            
            print("运行: python app/main.py")
            print("然后访问: http://localhost:8000")
            return "web"
        except Exception as e:
            print(f"❌ Web界面启动失败: {e}")
            return None
    
    else:
        print("❌ 无效选择")
        return None

def run_quick_test():
    """运行快速测试"""
    print("\n🧪 运行快速测试...")
    
    try:
        result = subprocess.run([
            sys.executable, "complete_notes_system.py"
        ], capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ 测试成功!")
            print("📁 查看输出目录: test_output/")
            print("📝 主要文件:")
            print("  - test_notes.md (Markdown格式)")
            print("  - test_notes.html (网页格式)")
            print("  - test_notes.json (数据格式)")
            
            # 尝试显示部分输出
            output_dir = Path("test_output")
            if output_dir.exists():
                md_file = output_dir / "test_notes.md"
                if md_file.exists():
                    print("\n📖 笔记预览:")
                    with open(md_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()[:10]  # 显示前10行
                        for line in lines:
                            print(f"  {line.rstrip()}")
                    print("  ...")
        else:
            print(f"❌ 测试失败:")
            print(result.stderr)
    
    except Exception as e:
        print(f"❌ 运行错误: {e}")

def show_system_info():
    """显示系统信息"""
    print("\n📊 系统信息:")
    print(f"  Python版本: {sys.version.split()[0]}")
    print(f"  工作目录: {os.getcwd()}")
    print(f"  系统平台: {sys.platform}")
    
    # 检查文件结构
    important_files = [
        "complete_notes_system.py",
        "practical_notes_formatter.py", 
        "robust_notes_processor.py",
        "app/main.py",
        "requirements.txt"
    ]
    
    print("\n📁 文件结构:")
    for file_path in important_files:
        path = Path(file_path)
        status = "✅" if path.exists() else "❌"
        print(f"  {status} {file_path}")

def main():
    """主函数"""
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请先安装必要的模块")
        return
    
    # 显示系统信息
    show_system_info()
    
    # 显示使用选项
    show_usage_options()
    
    # 交互式设置
    result = interactive_setup()
    
    if result == "test":
        run_quick_test()
    elif isinstance(result, tuple) and result[0] == "process":
        _, pdf_file, api_key = result
        print(f"\n🤖 将处理: {pdf_file}")
        print("请手动运行:")
        print(f'python complete_notes_system.py "{pdf_file}" --api-key {api_key}')
    elif result == "web":
        print("\n🌐 启动Web界面...")
        print("请手动运行: python app/main.py")
        print("然后访问: http://localhost:8000")
    
    print("\n" + "=" * 60)
    print("🎯 感谢使用实战笔记生成器!")
    print("💡 记住：我们的目标是帮你快速掌握知识点并能上手做题！")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作")
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")
        import traceback
        traceback.print_exc()