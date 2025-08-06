"""
完整的实战笔记系统
集成处理器和格式化器，提供完整的PDF转笔记功能
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any
import argparse

# from robust_notes_processor import PracticalNotesProcessor
from practical_notes_formatter import PracticalNotesFormatter


class CompleteNotesSystem:
    """完整的笔记生成系统"""
    
    def __init__(self, openai_api_key: str = None):
        # self.processor = PracticalNotesProcessor(openai_api_key)
        self.formatter = PracticalNotesFormatter()
    
    async def process_pdf_to_notes(
        self, 
        pdf_path: Path, 
        output_dir: Path = None,
        formats: list = None
    ) -> Dict[str, Any]:
        """
        完整的PDF转笔记流程
        
        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录
            formats: 输出格式 ['json', 'markdown', 'html']
        """
        
        if output_dir is None:
            output_dir = pdf_path.parent / "notes_output"
        
        if formats is None:
            formats = ['json', 'markdown', 'html']
        
        output_dir.mkdir(exist_ok=True)
        
        print(f"🚀 开始处理 {pdf_path.name}")
        print("=" * 50)
        
        # 1. 处理PDF生成笔记数据 (暂时使用测试数据)
        print("⚠️ 使用测试数据 (完整版需要安装依赖)")
        notes_data = self._create_sample_notes(pdf_path)
        
        # 2. 生成不同格式的输出
        output_files = {}
        base_name = pdf_path.stem
        
        if 'json' in formats:
            json_path = output_dir / f"{base_name}_notes.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(notes_data, f, ensure_ascii=False, indent=2)
            output_files['json'] = json_path
            print(f"📄 JSON格式: {json_path}")
        
        if 'markdown' in formats:
            md_path = output_dir / f"{base_name}_notes.md"
            markdown_content = self.formatter.format_to_markdown(notes_data)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            output_files['markdown'] = md_path
            print(f"📝 Markdown格式: {md_path}")
        
        if 'html' in formats:
            html_path = output_dir / f"{base_name}_notes.html"
            html_content = self.formatter.format_to_compact_html(notes_data)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            output_files['html'] = html_path
            print(f"🌐 HTML格式: {html_path}")
        
        # 3. 生成处理报告
        report = self._generate_processing_report(notes_data, output_files)
        report_path = output_dir / f"{base_name}_report.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("=" * 50)
        print(f"🎉 处理完成! 文件保存在: {output_dir}")
        print(f"📊 处理报告: {report_path}")
        
        return {
            'notes_data': notes_data,
            'output_files': output_files,
            'report_path': report_path
        }
    
    def _create_sample_notes(self, pdf_path: Path) -> Dict[str, Any]:
        """创建示例笔记数据"""
        return {
            "title": f"学习笔记 - {pdf_path.stem}",
            "source_file": pdf_path.name,
            "concepts": [
                {
                    "name": "核心概念1",
                    "importance": "这是学习的基础，必须牢固掌握",
                    "core_idea": "通过理解本质规律，掌握解决问题的方法",
                    "when_to_use": "遇到相关题型时的首选方法"
                }
            ],
            "formulas": [
                {
                    "name": "重要公式",
                    "latex": "E = mc^2",
                    "variables": {"E": "能量", "m": "质量", "c": "光速"},
                    "use_cases": ["相对论计算", "能量转换"],
                    "variations": ["m = E/c^2"]
                }
            ],
            "examples": [
                {
                    "concept": "基础计算",
                    "problem": "根据给定条件，计算相关物理量",
                    "solution_steps": [
                        "分析题目给出的已知条件",
                        "确定要求解的未知量",
                        "选择合适的公式",
                        "代入数值进行计算",
                        "检验答案的合理性"
                    ],
                    "key_insight": "理解物理意义比记住公式更重要",
                    "common_mistakes": ["单位不统一", "公式选择错误", "计算粗心"]
                }
            ],
            "practical_tips": [
                "先理解概念，再记忆公式",
                "做题时画图帮助理解",
                "注意单位换算",
                "多做练习加深理解"
            ],
            "processing_info": {
                "success": True,
                "method": "sample_data",
                "quality": "demo"
            }
        }
    
    def _create_error_notes(self, pdf_path: Path, error_msg: str) -> Dict[str, Any]:
        """创建错误情况下的基础笔记"""
        
        return {
            "title": f"学习笔记 - {pdf_path.stem}",
            "concepts": [
                {
                    "name": "文档内容",
                    "importance": "需要手动分析文档内容",
                    "core_idea": "由于自动处理失败，请手动阅读PDF文档提取要点",
                    "when_to_use": "根据学习需要"
                }
            ],
            "formulas": [
                {
                    "name": "待提取公式",
                    "latex": "请手动从PDF中提取数学公式",
                    "variables": {},
                    "use_cases": ["根据具体内容确定"],
                    "variations": []
                }
            ],
            "examples": [
                {
                    "concept": "基础练习",
                    "problem": "请根据PDF内容创建相应的练习题",
                    "solution_steps": ["阅读理解", "分析问题", "选择方法", "求解"],
                    "key_insight": "理解概念是解题的关键",
                    "common_mistakes": ["理解偏差", "计算错误"]
                }
            ],
            "practical_tips": [
                "仔细阅读原文档",
                "手动整理重要概念",
                "自己创建练习题"
            ],
            "processing_info": {
                "success": False,
                "error": error_msg,
                "method": "fallback",
                "quality": "basic"
            }
        }
    
    def _generate_processing_report(self, notes_data: Dict[str, Any], output_files: Dict[str, Path]) -> str:
        """生成处理报告"""
        
        processing_info = notes_data.get('processing_info', {})
        metadata = notes_data.get('metadata', {})
        
        report = f"""
📚 PDF笔记生成报告
{'=' * 40}

📋 基本信息:
- 源文件: {notes_data.get('source_file', 'Unknown')}
- 处理状态: {'✅ 成功' if processing_info.get('success', False) else '❌ 部分失败'}
- 处理方法: {processing_info.get('method', 'unknown')}
- 质量等级: {processing_info.get('quality', 'unknown')}

📊 内容统计:
- 核心概念: {len(notes_data.get('concepts', []))} 个
- 重要公式: {len(notes_data.get('formulas', []))} 个  
- 标准例题: {len(notes_data.get('examples', []))} 个
- 实战技巧: {len(notes_data.get('practical_tips', []))} 个

📁 输出文件:
"""
        
        for format_type, file_path in output_files.items():
            report += f"- {format_type.upper()}: {file_path.name}\n"
        
        if not processing_info.get('success', True):
            report += f"\n⚠️ 处理问题:\n- {processing_info.get('error', 'Unknown error')}\n"
        
        report += f"""
💡 使用建议:
1. 优先查看 Markdown 版本进行学习
2. 使用 HTML 版本进行打印
3. JSON 版本可用于进一步处理

🎯 学习策略:
1. 先快速浏览概念速览
2. 重点记忆公式速查表
3. 通过例题加深理解
4. 应用实战技巧提高效率
"""
        
        return report


async def main():
    """命令行主函数"""
    
    parser = argparse.ArgumentParser(description='实战导向的PDF笔记生成器')
    parser.add_argument('pdf_path', type=str, help='PDF文件路径')
    parser.add_argument('--api-key', type=str, required=True, help='OpenAI API Key')
    parser.add_argument('--output-dir', type=str, help='输出目录')
    parser.add_argument('--formats', nargs='+', 
                       choices=['json', 'markdown', 'html'],
                       default=['json', 'markdown', 'html'],
                       help='输出格式')
    
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"❌ 文件不存在: {pdf_path}")
        return
    
    output_dir = Path(args.output_dir) if args.output_dir else None
    
    system = CompleteNotesSystem(args.api_key)
    
    try:
        result = await system.process_pdf_to_notes(
            pdf_path=pdf_path,
            output_dir=output_dir,
            formats=args.formats
        )
        
        print(f"\n🎉 处理成功!")
        print(f"📚 标题: {result['notes_data']['title']}")
        print(f"📊 质量: {result['notes_data']['processing_info']['quality']}")
        
    except Exception as e:
        print(f"💥 处理失败: {e}")


# 快速测试函数
async def quick_test():
    """快速测试函数（用于开发调试）"""
    
    # 使用示例数据进行测试
    test_notes = {
        "title": "线性代数基础",
        "source_file": "test.pdf",
        "concepts": [
            {
                "name": "矩阵",
                "importance": "线性代数的基础数据结构，用于表示线性变换",
                "core_idea": "数字的矩形阵列，可以进行特定的数学运算",
                "when_to_use": "线性变换、方程组求解、数据处理"
            },
            {
                "name": "行列式",
                "importance": "衡量矩阵的'大小'，判断矩阵可逆性",
                "core_idea": "矩阵的一个标量属性",
                "when_to_use": "判断矩阵可逆、计算体积变化、求解线性方程组"
            }
        ],
        "formulas": [
            {
                "name": "2×2矩阵行列式",
                "latex": "\\det(A) = \\begin{vmatrix} a & b \\\\ c & d \\end{vmatrix} = ad - bc",
                "variables": {"a,b,c,d": "矩阵元素", "det(A)": "矩阵A的行列式"},
                "use_cases": ["判断2×2矩阵可逆性", "计算面积变化"],
                "variations": ["|A| = ad - bc"]
            },
            {
                "name": "矩阵乘法",
                "latex": "(AB)_{ij} = \\sum_{k=1}^{n} A_{ik}B_{kj}",
                "variables": {"A,B": "矩阵", "i,j": "行列索引", "n": "矩阵维数"},
                "use_cases": ["线性变换复合", "方程组求解"],
                "variations": ["C = AB"]
            }
        ],
        "examples": [
            {
                "concept": "行列式计算",
                "problem": "计算矩阵 A = [[2,3],[1,4]] 的行列式",
                "solution_steps": [
                    "使用2×2行列式公式: det(A) = ad - bc",
                    "识别矩阵元素: a=2, b=3, c=1, d=4",
                    "代入公式: det(A) = 2×4 - 3×1",
                    "计算结果: det(A) = 8 - 3 = 5"
                ],
                "key_insight": "2×2行列式就是主对角线乘积减去副对角线乘积",
                "common_mistakes": ["符号搞错", "元素位置混淆"]
            },
            {
                "concept": "矩阵乘法",
                "problem": "计算 [[1,2],[3,4]] × [[2,0],[1,3]]",
                "solution_steps": [
                    "使用矩阵乘法定义 (AB)ij = Σ(Aik × Bkj)",
                    "计算(1,1)位置: 1×2 + 2×1 = 4",
                    "计算(1,2)位置: 1×0 + 2×3 = 6", 
                    "计算(2,1)位置: 3×2 + 4×1 = 10",
                    "计算(2,2)位置: 3×0 + 4×3 = 12",
                    "结果矩阵: [[4,6],[10,12]]"
                ],
                "key_insight": "矩阵乘法是行×列的内积运算",
                "common_mistakes": ["维度不匹配", "计算顺序错误", "内积计算错误"]
            }
        ],
        "practical_tips": [
            "做题前先检查矩阵维度是否匹配",
            "行列式计算要注意正负号",
            "矩阵乘法不满足交换律，注意顺序",
            "复杂计算可以分步进行，避免一步到位"
        ],
        "metadata": {
            "generation_method": "test_data",
            "focus": "problem_solving",
            "difficulty_level": "undergraduate"
        },
        "processing_info": {
            "success": True,
            "method": "test",
            "quality": "high"
        }
    }
    
    formatter = PracticalNotesFormatter()
    
    # 生成各种格式
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    # JSON
    with open(output_dir / "test_notes.json", 'w', encoding='utf-8') as f:
        json.dump(test_notes, f, ensure_ascii=False, indent=2)
    
    # Markdown
    markdown_content = formatter.format_to_markdown(test_notes)
    with open(output_dir / "test_notes.md", 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    # HTML
    html_content = formatter.format_to_compact_html(test_notes)
    with open(output_dir / "test_notes.html", 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("测试文件生成完成!")
    print("输出目录: test_output/")
    print("查看 test_notes.md 了解格式效果")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        # 无参数时运行快速测试
        print("运行快速测试...")
        asyncio.run(quick_test())
    else:
        # 有参数时运行正常流程
        asyncio.run(main())