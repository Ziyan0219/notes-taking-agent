# 实战笔记生成器 📚

一个**以做题为导向**的AI驱动系统，将PDF学习材料转换为紧凑实用的学习笔记。专注于本科难度，快速上手做题。

## 🎯 核心特色

- **📐 公式完整** - 多种模式识别，确保不遗漏重要公式
- **🎯 实战导向** - 重点说明"什么时候用"、"常见错误"
- **📝 本科难度** - 例题设计适中，可直接练手  
- **🚀 快速上手** - 紧凑排版，突出解题要点
- **💰 成本可控** - 单次AI调用，避免多轮消耗

## 🏗️ 系统架构

### 新架构 (鲁棒版本) - **推荐使用**
```
PDF输入 → [并行内容提取] → AI笔记生成 → 多格式输出
   ↓           ↓              ↓           ↓
PDF解析    公式识别        单次调用     JSON/MD/HTML
图片OCR    文本分析        GPT-4       完整笔记
表格提取    结构识别        生成笔记
```

### 原架构 (复杂版本) - 仅供参考
```
PDF → 结构分析 → 公式提取 → 笔记生成 → 练习生成 → 输出
      (AI调用)   (AI调用)   (AI调用)   (AI调用)
```

## 🤖 AI介入点说明

### 1. 新系统 - 单点AI介入
- **位置**: 内容分析后的笔记生成阶段
- **模型**: GPT-4 (可选GPT-3.5)
- **输入**: 提取的文本内容 + 识别的公式
- **输出**: 完整的结构化学习笔记
- **成本**: 约 $0.10-0.50 每个PDF (取决于内容长度)

### 2. 原系统 - 多点AI介入  
- **结构分析**: 识别章节和主题 (GPT-3.5)
- **公式增强**: 分析公式含义和应用 (GPT-3.5)  
- **练习生成**: 创建针对性习题 (GPT-3.5)
- **综合练习**: 多概念组合题目 (GPT-3.5)
- **成本**: 约 $1-3 每个PDF

## 🚀 快速开始

### 方案一：测试运行 (无需API Key)
```bash
# 1. 进入项目目录
cd notes-taking-agent

# 2. 运行测试 (生成示例笔记)
python complete_notes_system.py

# 3. 查看生成的笔记
# - test_output/test_notes.md (Markdown版本)
# - test_output/test_notes.html (HTML版本，适合打印)
# - test_output/test_notes.json (原始数据)
```

### 方案二：完整功能 (需要API Key)
```bash
# 1. 安装依赖
pip install openai PyMuPDF python-dotenv

# 2. 设置API Key
export OPENAI_API_KEY="your-api-key-here"
# Windows: set OPENAI_API_KEY=your-api-key-here

# 3. 处理PDF文件
python complete_notes_system.py your_file.pdf --api-key YOUR_KEY

# 4. 可选参数
python complete_notes_system.py file.pdf \
    --api-key YOUR_KEY \
    --output-dir custom_output \
    --formats markdown html
```

### 方案三：使用原Web界面
```bash
# 1. 启动Web服务
python app/main.py
# 或者
python start_app.py

# 2. 访问 http://localhost:8000
# 3. 上传PDF并等待处理
```

## 📁 项目结构

```
notes-taking-agent/
├── 🆕 complete_notes_system.py      # 新系统主程序
├── 🆕 robust_notes_processor.py     # 鲁棒PDF处理器  
├── 🆕 practical_notes_formatter.py  # 实战笔记格式化器
├── 
├── app/                             # 原Web应用
│   ├── main.py                      # FastAPI应用入口
│   ├── agents/                      # LangGraph代理
│   │   ├── notes_agent.py          # 笔记生成代理
│   │   └── agent_manager.py        # 代理管理器
│   ├── services/                    # 核心服务
│   │   ├── pdf_parser.py           # PDF解析
│   │   ├── content_analyzer.py     # 内容分析 (AI介入)
│   │   └── enhanced_note_generator.py # 增强笔记生成 (AI介入)
│   └── models/schemas.py            # 数据模型
├── 
├── requirements.txt                 # 依赖列表
├── start_app.py                    # 启动脚本
├── run_tests.py                    # 测试脚本
└── 🆕 README_NEW.md                # 本文档
```

## 📝 输出格式展示

生成的笔记包含以下结构化内容：

### 1. 内容概览
```markdown
## 📊 内容概览
| 项目 | 数量 | 说明 |
|------|------|------|
| 核心概念 | 3 | 必须掌握的基本概念 |
| 重要公式 | 5 | 做题必备公式清单 |
| 标准例题 | 4 | 本科难度练习题 |
```

### 2. 核心概念速览
```markdown
### 1. 导数
**💡 为什么重要**: 描述函数变化率，是微积分的核心概念
**🎯 核心思想**: 函数在某点的瞬时变化率  
**🔧 什么时候用**: 求切线斜率、最值问题、变化率分析
```

### 3. 公式速查表
```markdown
### 1. 导数定义
**公式**: $f'(x) = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}$

**变量说明**:
- $f'(x)$: f(x)在x处的导数
- $h$: 增量

**使用场景**:
- 求导数定义
- 证明导数性质
```

### 4. 标准例题
```markdown
### 例题 1 (导数计算)
**📋 题目**: 求 f(x) = x² 在 x=2 处的导数

**📝 解题步骤**:
1. 使用导数定义公式
2. f'(2) = lim[h→0] [(2+h)² - 4]/h
3. 展开: lim[h→0] [4+4h+h² - 4]/h
4. 求极限: f'(2) = 4

**💡 关键思路**: 二次函数的导数是一次函数
**⚠️ 常见错误**: 忘记求极限、计算错误
```

## 🔧 系统配置

### 环境变量设置
```bash
# .env 文件 (如果使用Web界面)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=True
```

### 成本控制选项
```python
# 在 robust_notes_processor.py 中修改
class CostOptimizedProcessor:
    def __init__(self):
        self.cheap_model = "gpt-3.5-turbo"    # 省钱版
        self.good_model = "gpt-4"             # 效果版
        self.budget_threshold = 1.0           # 成本阈值
```

## 📊 性能对比

| 指标 | 新系统(鲁棒) | 原系统(LangGraph) |
|------|-------------|-------------------|
| **处理时间** | 30-60秒 | 2-5分钟 |
| **API调用次数** | 1次 | 4-7次 |
| **平均成本** | $0.10-0.50 | $1-3 |
| **成功率** | >95% | ~70% |
| **输出质量** | 实战导向 | 学术风格 |

## 🐛 故障排除

### 常见问题

**1. 模块导入错误**
```bash
ModuleNotFoundError: No module named 'fitz'
```
解决：`pip install PyMuPDF`

**2. API Key错误**  
```bash
openai.AuthenticationError: Invalid API key
```
解决：检查 `OPENAI_API_KEY` 环境变量

**3. 编码错误 (Windows)**
```bash
UnicodeEncodeError: 'gbk' codec can't encode
```
解决：在命令行运行 `chcp 65001` 或使用PowerShell

**4. 内存不足**
```bash
OutOfMemoryError
```
解决：处理大文件时分批处理，或增加虚拟内存

### 降级运行模式

如果AI调用失败，系统会自动降级：
1. **Level 1**: AI生成完整笔记
2. **Level 2**: 模板式笔记生成  
3. **Level 3**: 基础文本整理 (总是成功)

## 🎯 使用建议

### 适合的文档类型
✅ **效果很好**:
- 数学/物理教科书
- 工程技术手册
- 包含公式的学术论文
- 结构化的课件PPT转PDF

⚠️ **效果一般**:
- 纯文字小说
- 扫描质量差的PDF
- 图片为主的文档
- 非结构化内容

### 最佳实践
1. **预处理PDF**: 确保文字清晰，公式可识别
2. **选择模型**: 重要内容用GPT-4，一般内容用GPT-3.5
3. **批量处理**: 多个文件可以写脚本批量处理
4. **二次编辑**: AI生成后可以手动调整完善

## 🚧 开发计划

- [ ] 支持更多PDF格式 (扫描版、加密PDF)
- [ ] 增加图片中公式的OCR识别
- [ ] 支持中文数学符号识别
- [ ] 添加交互式练习模式
- [ ] 集成Anki卡片导出功能

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

优先需要的改进：
1. 公式识别准确率提升
2. 更多学科的模板支持
3. 移动端适配
4. 离线模式支持

---

## 📞 技术支持

- **快速测试**: 直接运行 `python complete_notes_system.py`
- **完整功能**: 需要OpenAI API Key
- **问题反馈**: 请提供PDF示例和错误日志

**记住**: 这个系统的目标是帮你快速掌握知识点并能上手做题，而不是生成完美的学术论文！