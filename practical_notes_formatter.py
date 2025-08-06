"""
实战笔记格式化器
生成紧凑、实用的学习笔记
"""

from typing import Dict, Any, List
import json
import re


class PracticalNotesFormatter:
    """实战笔记格式化器 - 生成紧凑易用的笔记"""
    
    def __init__(self):
        self.difficulty_icons = {
            "basic": "🟢",
            "intermediate": "🟡", 
            "advanced": "🔴"
        }
    
    def format_to_markdown(self, notes_data: Dict[str, Any]) -> str:
        """转换为Markdown格式"""
        
        md_parts = []
        
        # 标题和概览
        md_parts.append(self._format_header(notes_data))
        
        # 核心概念速览
        md_parts.append(self._format_concepts_summary(notes_data.get('concepts', [])))
        
        # 公式速查表
        md_parts.append(self._format_formulas_reference(notes_data.get('formulas', [])))
        
        # 标准例题
        md_parts.append(self._format_examples(notes_data.get('examples', [])))
        
        # 实战技巧
        md_parts.append(self._format_practical_tips(notes_data.get('practical_tips', [])))
        
        return '\n\n'.join(md_parts)
    
    def _format_header(self, notes_data: Dict[str, Any]) -> str:
        """格式化标题部分"""
        
        title = notes_data.get('title', '学习笔记')
        metadata = notes_data.get('metadata', {})
        
        header = f"""# {title}

## 📊 内容概览
| 项目 | 数量 | 说明 |
|------|------|------|
| 核心概念 | {len(notes_data.get('concepts', []))} | 必须掌握的基本概念 |
| 重要公式 | {len(notes_data.get('formulas', []))} | 做题必备公式清单 |
| 标准例题 | {len(notes_data.get('examples', []))} | 本科难度练习题 |

> 🎯 **学习目标**: 快速掌握核心概念，熟练运用公式解题"""
        
        return header
    
    def _format_concepts_summary(self, concepts: List[Dict[str, Any]]) -> str:
        """格式化概念速览"""
        
        if not concepts:
            return ""
        
        md = "## 🧠 核心概念速览\n\n"
        
        for i, concept in enumerate(concepts, 1):
            name = concept.get('name', f'概念{i}')
            importance = concept.get('importance', '')
            core_idea = concept.get('core_idea', '')
            when_to_use = concept.get('when_to_use', '')
            
            md += f"""### {i}. {name}

**💡 为什么重要**: {importance}

**🎯 核心思想**: {core_idea}

**🔧 什么时候用**: {when_to_use}

---

"""
        
        return md
    
    def _format_formulas_reference(self, formulas: List[Dict[str, Any]]) -> str:
        """格式化公式速查表"""
        
        if not formulas:
            return ""
        
        md = "## 📐 公式速查表\n\n"
        md += "> 💡 **使用提示**: 做题时先判断题型，再选择对应公式\n\n"
        
        for i, formula in enumerate(formulas, 1):
            name = formula.get('name', f'公式{i}')
            latex = formula.get('latex', '')
            variables = formula.get('variables', {})
            use_cases = formula.get('use_cases', [])
            variations = formula.get('variations', [])
            
            md += f"""### {i}. {name}

**公式**: ${latex}$

"""
            
            # 变量说明
            if variables:
                md += "**变量说明**:\n"
                for var, meaning in variables.items():
                    md += f"- ${var}$: {meaning}\n"
                md += "\n"
            
            # 使用场景
            if use_cases:
                md += "**使用场景**:\n"
                for case in use_cases:
                    md += f"- {case}\n"
                md += "\n"
            
            # 常见变形
            if variations:
                md += "**常见变形**:\n"
                for var in variations:
                    md += f"- ${var}$\n"
                md += "\n"
            
            md += "---\n\n"
        
        return md
    
    def _format_examples(self, examples: List[Dict[str, Any]]) -> str:
        """格式化标准例题"""
        
        if not examples:
            return ""
        
        md = "## 📝 标准例题\n\n"
        md += "> 🎯 **练习目标**: 熟练掌握解题步骤和思路\n\n"
        
        for i, example in enumerate(examples, 1):
            concept = example.get('concept', '')
            problem = example.get('problem', '')
            solution_steps = example.get('solution_steps', [])
            key_insight = example.get('key_insight', '')
            common_mistakes = example.get('common_mistakes', [])
            
            md += f"""### 例题 {i} {f'({concept})' if concept else ''}

**📋 题目**: {problem}

**📝 解题步骤**:
"""
            
            for j, step in enumerate(solution_steps, 1):
                md += f"{j}. {step}\n"
            
            if key_insight:
                md += f"\n**💡 关键思路**: {key_insight}\n"
            
            if common_mistakes:
                md += f"\n**⚠️ 常见错误**:\n"
                for mistake in common_mistakes:
                    md += f"- {mistake}\n"
            
            md += "\n---\n\n"
        
        return md
    
    def _format_practical_tips(self, tips: List[str]) -> str:
        """格式化实战技巧"""
        
        if not tips:
            return ""
        
        md = "## 🚀 实战技巧\n\n"
        md += "> 💪 **做题必备**: 掌握这些技巧，提高解题效率\n\n"
        
        for i, tip in enumerate(tips, 1):
            md += f"{i}. **{tip}**\n\n"
        
        return md
    
    def format_to_compact_html(self, notes_data: Dict[str, Any]) -> str:
        """生成紧凑的HTML版本（适合打印）"""
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{notes_data.get('title', '学习笔记')}</title>
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            line-height: 1.4;
            margin: 20px;
            font-size: 14px;
        }}
        .header {{
            border-bottom: 2px solid #007acc;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .concept-card {{
            background: #f8f9fa;
            border-left: 4px solid #28a745;
            padding: 10px;
            margin: 10px 0;
        }}
        .formula-box {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .example-box {{
            background: #e7f3ff;
            border-left: 4px solid #007acc;
            padding: 10px;
            margin: 10px 0;
        }}
        .tip {{
            background: #d4edda;
            border: 1px solid #c3e6cb;
            padding: 8px;
            margin: 5px 0;
            border-radius: 4px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 10px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        .compact {{
            margin: 5px 0;
        }}
        h1 {{ color: #333; font-size: 24px; }}
        h2 {{ color: #007acc; font-size: 18px; border-bottom: 1px solid #ddd; }}
        h3 {{ color: #666; font-size: 16px; }}
    </style>
</head>
<body>
"""
        
        # 转换markdown为HTML
        markdown_content = self.format_to_markdown(notes_data)
        
        # 简单的markdown转HTML（可以用更专业的库）
        html_content = self._simple_markdown_to_html(markdown_content)
        
        html += html_content + "\n</body>\n</html>"
        
        return html
    
    def _simple_markdown_to_html(self, markdown: str) -> str:
        """简单的Markdown转HTML"""
        
        html = markdown
        
        # 标题转换
        html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # 表格转换（简化版）
        # 这里可以添加更完善的表格转换逻辑
        
        # 段落
        html = re.sub(r'\n\n', '</p>\n<p>', html)
        html = f'<p>{html}</p>'
        
        # 列表
        html = re.sub(r'^- (.*?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)
        
        return html


# 使用示例
def demo_formatter():
    """演示格式化器的使用"""
    
    # 示例数据
    sample_notes = {
        "title": "微积分基础",
        "concepts": [
            {
                "name": "导数",
                "importance": "描述函数变化率，是微积分的核心概念",
                "core_idea": "函数在某点的瞬时变化率",
                "when_to_use": "求切线斜率、最值问题、变化率分析"
            }
        ],
        "formulas": [
            {
                "name": "导数定义",
                "latex": "f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}",
                "variables": {"f'(x)": "f(x)在x处的导数", "h": "增量"},
                "use_cases": ["求导数定义", "证明导数性质"],
                "variations": ["f'(x) = \\frac{df}{dx}"]
            }
        ],
        "examples": [
            {
                "concept": "导数计算",
                "problem": "求 f(x) = x² 在 x=2 处的导数",
                "solution_steps": [
                    "使用导数定义公式",
                    "f'(2) = lim[h→0] [(2+h)² - 4]/h",
                    "展开: lim[h→0] [4+4h+h² - 4]/h",
                    "化简: lim[h→0] (4h+h²)/h = lim[h→0] (4+h)",
                    "求极限: f'(2) = 4"
                ],
                "key_insight": "二次函数的导数是一次函数",
                "common_mistakes": ["忘记求极限", "计算错误"]
            }
        ],
        "practical_tips": [
            "先判断函数类型，选择合适的求导公式",
            "复合函数要用链式法则",
            "最后检查答案的合理性"
        ]
    }
    
    formatter = PracticalNotesFormatter()
    
    # 生成Markdown
    markdown_output = formatter.format_to_markdown(sample_notes)
    print("Markdown输出:")
    print(markdown_output)
    
    # 生成HTML
    html_output = formatter.format_to_compact_html(sample_notes)
    
    # 保存文件
    with open('sample_notes.md', 'w', encoding='utf-8') as f:
        f.write(markdown_output)
    
    with open('sample_notes.html', 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    print("\n✅ 文件已生成: sample_notes.md 和 sample_notes.html")


if __name__ == "__main__":
    demo_formatter()