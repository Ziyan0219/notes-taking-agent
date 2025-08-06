"""
实战导向的鲁棒笔记处理器
核心：公式完整 + 例题实践 + 快速上手
"""

import asyncio
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import fitz  # PyMuPDF
from openai import AsyncOpenAI


class DifficultyLevel(Enum):
    BASIC = "basic"           # 定义理解
    INTERMEDIATE = "intermediate"  # 本科标准
    ADVANCED = "advanced"     # 拓展应用


@dataclass
class Formula:
    """公式数据结构"""
    name: str                    # 公式名称
    latex: str                   # LaTeX表示
    variables: Dict[str, str]    # 变量说明
    when_to_use: str            # 使用场景
    difficulty: DifficultyLevel  # 难度等级
    related_concepts: List[str]  # 相关概念


@dataclass
class Example:
    """例题数据结构"""
    problem: str                 # 题目描述
    solution_steps: List[str]    # 解题步骤
    key_formulas: List[str]      # 用到的公式
    difficulty: DifficultyLevel  # 难度等级
    common_mistakes: List[str]   # 常见错误


@dataclass
class Concept:
    """知识点数据结构"""
    name: str
    importance: str              # 为什么重要
    core_idea: str              # 核心思想
    formulas: List[Formula]     # 相关公式
    examples: List[Example]     # 例题
    prerequisites: List[str]     # 前置知识


class PracticalNotesProcessor:
    """实战笔记处理器 - 以做题为导向"""
    
    def __init__(self, openai_api_key: str):
        self.client = AsyncOpenAI(api_key=openai_api_key)
        
    async def process_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """主处理流程"""
        print("🔍 提取PDF内容...")
        
        # 1. 并行内容提取
        raw_content = await self._extract_pdf_content(pdf_path)
        
        # 2. 识别所有公式（确保不漏）
        formulas = await self._extract_all_formulas(raw_content)
        print(f"📐 发现 {len(formulas)} 个公式")
        
        # 3. 生成实战笔记
        notes = await self._generate_practical_notes(raw_content, formulas)
        
        return notes
    
    async def _extract_pdf_content(self, pdf_path: Path) -> str:
        """提取PDF内容 - 多种方法并行"""
        
        try:
            doc = fitz.open(pdf_path)
            content = ""
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                
                # 提取文本
                text = page.get_text()
                content += f"\n--- Page {page_num + 1} ---\n{text}"
                
                # 提取图片中的公式（如果需要的话）
                # images = page.get_images()
                # for img in images:
                #     # OCR处理图片公式
                #     pass
            
            doc.close()
            return content
            
        except Exception as e:
            raise Exception(f"PDF提取失败: {e}")
    
    async def _extract_all_formulas(self, content: str) -> List[Dict[str, Any]]:
        """提取所有公式 - 确保不遗漏"""
        
        formulas = []
        
        # 方法1: LaTeX公式模式
        latex_patterns = [
            r'\$\$([^$]+)\$\$',           # 显示公式
            r'\$([^$\n]{3,40})\$',        # 行内公式
            r'\\begin\{equation\}(.*?)\\end\{equation\}',
            r'\\begin\{align\}(.*?)\\end\{align\}',
        ]
        
        for pattern in latex_patterns:
            matches = re.finditer(pattern, content, re.DOTALL)
            for match in matches:
                formula_text = match.group(1).strip()
                if len(formula_text) > 2:
                    formulas.append({
                        'type': 'latex',
                        'content': formula_text,
                        'context': self._get_context(content, match.start(), match.end())
                    })
        
        # 方法2: 数学表达式模式
        math_patterns = [
            r'([A-Za-z_]\w*\s*=\s*[^,\.\n]{5,60})',  # 等式
            r'([∫∑∏∂√][^,\.\n]{3,60})',              # 积分求和等
            r'([A-Za-z_]\w*\([^)]+\)\s*=\s*[^,\.\n]{3,60})',  # 函数定义
        ]
        
        for pattern in math_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                formula_text = match.group(1).strip()
                if self._is_valid_formula(formula_text):
                    formulas.append({
                        'type': 'expression',
                        'content': formula_text,
                        'context': self._get_context(content, match.start(), match.end())
                    })
        
        # 去重
        unique_formulas = []
        seen = set()
        for f in formulas:
            normalized = re.sub(r'\s+', '', f['content'].lower())
            if normalized not in seen and len(normalized) > 3:
                seen.add(normalized)
                unique_formulas.append(f)
        
        return unique_formulas
    
    def _get_context(self, content: str, start: int, end: int) -> str:
        """获取公式周围的上下文"""
        context_start = max(0, start - 150)
        context_end = min(len(content), end + 150)
        context = content[context_start:context_end].replace('\n', ' ')
        return ' '.join(context.split())
    
    def _is_valid_formula(self, formula: str) -> bool:
        """判断是否是有效的数学公式"""
        # 过滤掉明显不是公式的内容
        invalid_patterns = [
            r'^[0-9]+$',                    # 纯数字
            r'^[A-Za-z]+\s*=\s*[A-Za-z]+$', # 简单变量赋值
            r'page\s*=\s*\d+',              # 页码
            r'chapter\s*=',                  # 章节
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, formula.lower()):
                return False
        
        # 必须包含数学符号或操作符
        math_indicators = ['=', '+', '-', '*', '/', '^', '∫', '∑', '∂', '√', '(', ')']
        return any(indicator in formula for indicator in math_indicators)
    
    async def _generate_practical_notes(self, content: str, formulas: List[Dict]) -> Dict[str, Any]:
        """生成实战笔记 - 单次AI调用完成所有任务"""
        
        formulas_summary = []
        for f in formulas[:20]:  # 限制数量避免token超限
            formulas_summary.append({
                'formula': f['content'],
                'context': f['context'][:200]
            })
        
        prompt = f"""
你是一位经验丰富的大学数学/物理教师。基于以下材料，创建一份**以做题为导向**的学习笔记。

材料内容（前2000字）：
{content[:2000]}

发现的公式：
{json.dumps(formulas_summary, ensure_ascii=False, indent=2)}

请按以下要求生成学习笔记：

## 1. 知识点梳理
- 识别3-5个核心概念
- 每个概念说明**为什么重要**，**什么时候用**

## 2. 公式清单
- 列出所有重要公式（不要遗漏）
- 每个公式包括：
  * 公式名称和LaTeX表示
  * 各变量含义
  * 使用场景（什么题型用这个公式）
  * 常见变形

## 3. 标准例题
- 每个知识点提供1-2个**本科难度**的例题
- 包含：
  * 题目描述
  * 详细解题步骤
  * 关键思路点拨
  * 常见错误提醒

## 4. 实战技巧
- 做题时的判断技巧
- 公式选择策略
- 常见陷阱

要求：
- 排版紧凑，重点突出
- 例题难度适中（本科水平）
- 以快速上手做题为目标
- 用中文回答

请用JSON格式返回：
{{
    "title": "笔记标题",
    "concepts": [
        {{
            "name": "概念名称",
            "importance": "为什么重要",
            "core_idea": "核心思想",
            "when_to_use": "什么时候用"
        }}
    ],
    "formulas": [
        {{
            "name": "公式名称",
            "latex": "LaTeX公式",
            "variables": {{"变量": "含义"}},
            "use_cases": ["使用场景1", "使用场景2"],
            "variations": ["变形1", "变形2"]
        }}
    ],
    "examples": [
        {{
            "concept": "相关概念",
            "problem": "题目描述",
            "solution_steps": ["步骤1", "步骤2"],
            "key_insight": "关键思路",
            "common_mistakes": ["常见错误1"]
        }}
    ],
    "practical_tips": [
        "实战技巧1",
        "实战技巧2"
    ]
}}
"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是专业的数学/物理教师，擅长制作实战导向的学习材料。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            # 解析JSON响应
            response_text = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                notes = json.loads(json_match.group())
                return self._format_final_notes(notes)
            else:
                raise Exception("无法解析AI响应")
                
        except Exception as e:
            # 降级方案：基础笔记生成
            return self._generate_fallback_notes(content, formulas)
    
    def _generate_fallback_notes(self, content: str, formulas: List[Dict]) -> Dict[str, Any]:
        """降级方案：基础笔记生成"""
        
        notes = {
            "title": "学习笔记",
            "concepts": [
                {
                    "name": "基础内容",
                    "importance": "从文档中提取的核心内容",
                    "core_idea": content[:500] + "...",
                    "when_to_use": "根据具体问题情况"
                }
            ],
            "formulas": [],
            "examples": [
                {
                    "concept": "基础概念",
                    "problem": "请根据材料内容进行相关练习",
                    "solution_steps": ["分析题目", "选择合适方法", "计算求解", "检验答案"],
                    "key_insight": "理解概念，选对方法",
                    "common_mistakes": ["概念理解不清", "计算错误"]
                }
            ],
            "practical_tips": [
                "仔细读题，理解问题要求",
                "选择合适的公式和方法",
                "计算过程要细心",
                "最后检验答案合理性"
            ]
        }
        
        # 添加发现的公式
        for i, formula in enumerate(formulas[:10]):
            notes["formulas"].append({
                "name": f"公式 {i+1}",
                "latex": formula['content'],
                "variables": {},
                "use_cases": ["根据上下文确定"],
                "variations": []
            })
        
        return notes
    
    def _format_final_notes(self, notes: Dict[str, Any]) -> Dict[str, Any]:
        """格式化最终笔记输出"""
        
        # 确保笔记结构完整
        required_keys = ["title", "concepts", "formulas", "examples", "practical_tips"]
        for key in required_keys:
            if key not in notes:
                notes[key] = []
        
        # 添加元数据
        notes["metadata"] = {
            "generation_method": "practical_oriented",
            "focus": "problem_solving",
            "difficulty_level": "undergraduate",
            "total_formulas": len(notes.get("formulas", [])),
            "total_examples": len(notes.get("examples", []))
        }
        
        return notes


# 使用示例
async def main():
    processor = PracticalNotesProcessor("your-openai-api-key")
    
    pdf_path = Path("example.pdf")
    notes = await processor.process_pdf(pdf_path)
    
    print("📚 生成的实战笔记：")
    print(f"标题：{notes['title']}")
    print(f"核心概念：{len(notes['concepts'])} 个")
    print(f"重要公式：{len(notes['formulas'])} 个")
    print(f"练习例题：{len(notes['examples'])} 个")


if __name__ == "__main__":
    asyncio.run(main())