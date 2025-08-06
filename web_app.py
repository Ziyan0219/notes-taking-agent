"""
现代化Web笔记生成器
基于新的鲁棒系统，提供可视化笔记界面
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import json
import asyncio
from pathlib import Path
import shutil
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# 导入我们的鲁棒处理系统
try:
    from robust_notes_processor import PracticalNotesProcessor
    from practical_notes_formatter import PracticalNotesFormatter
    SYSTEM_AVAILABLE = True
except ImportError:
    SYSTEM_AVAILABLE = False
    print("⚠️ 鲁棒处理系统未安装，使用模拟模式")

app = FastAPI(
    title="实战笔记生成器",
    description="上传PDF，生成实战导向的可视化学习笔记",
    version="2.0"
)

# 创建必要的目录
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("generated_notes") 
STATIC_DIR = Path("static_web")
TEMPLATE_DIR = Path("templates_web")

for dir_path in [UPLOAD_DIR, OUTPUT_DIR, STATIC_DIR, TEMPLATE_DIR]:
    dir_path.mkdir(exist_ok=True)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 模板引擎
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# 全局存储处理状态
processing_jobs: Dict[str, Dict[str, Any]] = {}

# 初始化处理器
if SYSTEM_AVAILABLE:
    processor = None
    formatter = PracticalNotesFormatter()
else:
    processor = None
    formatter = None


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """主页面 - 上传界面"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "system_available": SYSTEM_AVAILABLE
    })


@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    api_key: str = Form(default=""),
    use_gpt4: bool = Form(default=False)
):
    """上传PDF文件并开始处理"""
    
    # 验证文件
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持PDF文件")
    
    if len(await file.read()) > 50 * 1024 * 1024:  # 50MB限制
        raise HTTPException(status_code=400, detail="文件过大，最大支持50MB")
    
    await file.seek(0)  # 重置文件指针
    
    # 生成任务ID
    job_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存文件
    file_path = UPLOAD_DIR / f"{timestamp}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 初始化任务状态
    processing_jobs[job_id] = {
        "filename": file.filename,
        "file_path": str(file_path),
        "status": "pending",
        "progress": 0,
        "message": "任务已提交",
        "created_at": datetime.now().isoformat(),
        "api_key": api_key,
        "use_gpt4": use_gpt4,
        "result": None
    }
    
    # 启动后台处理
    asyncio.create_task(process_pdf_background(job_id, file_path, api_key, use_gpt4))
    
    return JSONResponse({
        "job_id": job_id,
        "message": "文件上传成功，开始处理",
        "filename": file.filename
    })


async def process_pdf_background(job_id: str, file_path: Path, api_key: str, use_gpt4: bool):
    """后台处理PDF"""
    
    try:
        # 更新状态
        processing_jobs[job_id]["status"] = "processing"
        processing_jobs[job_id]["progress"] = 10
        processing_jobs[job_id]["message"] = "开始分析PDF内容"
        
        if SYSTEM_AVAILABLE and api_key.strip():
            # 使用真实的AI处理
            global processor
            if processor is None:
                processor = PracticalNotesProcessor(api_key)
            
            processing_jobs[job_id]["progress"] = 30
            processing_jobs[job_id]["message"] = "AI分析中..."
            
            # 调用处理系统
            notes_data = await processor.process_pdf(file_path)
            
            processing_jobs[job_id]["progress"] = 80
            processing_jobs[job_id]["message"] = "生成可视化笔记"
            
        else:
            # 使用示例数据
            processing_jobs[job_id]["progress"] = 50
            processing_jobs[job_id]["message"] = "生成示例笔记"
            
            await asyncio.sleep(2)  # 模拟处理时间
            
            notes_data = create_sample_notes_data(file_path.stem)
        
        # 生成输出文件
        output_base = OUTPUT_DIR / f"notes_{job_id}"
        
        # 保存JSON
        json_path = f"{output_base}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(notes_data, f, ensure_ascii=False, indent=2)
        
        # 生成HTML (如果formatter可用)
        html_path = None
        if formatter:
            html_content = formatter.format_to_compact_html(notes_data)
            html_path = f"{output_base}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        # 更新完成状态
        processing_jobs[job_id].update({
            "status": "completed",
            "progress": 100,
            "message": "处理完成",
            "result": {
                "notes_data": notes_data,
                "json_path": json_path,
                "html_path": html_path,
                "title": notes_data.get("title", "学习笔记")
            }
        })
        
    except Exception as e:
        # 处理错误
        processing_jobs[job_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"处理失败: {str(e)}",
            "error": str(e)
        })


def create_sample_notes_data(filename: str) -> Dict[str, Any]:
    """创建示例笔记数据"""
    return {
        "title": f"学习笔记 - {filename}",
        "source_file": filename,
        "concepts": [
            {
                "name": "微分方程",
                "importance": "描述物理系统变化规律的数学工具",
                "core_idea": "函数与其导数之间的关系",
                "when_to_use": "物理建模、工程分析、经济预测"
            },
            {
                "name": "拉普拉斯变换",
                "importance": "求解微分方程的强大工具",
                "core_idea": "将微分方程转化为代数方程",
                "when_to_use": "线性微分方程、控制系统分析"
            }
        ],
        "formulas": [
            {
                "name": "一阶线性微分方程",
                "latex": "\\frac{dy}{dx} + P(x)y = Q(x)",
                "variables": {
                    "y": "未知函数",
                    "P(x)": "系数函数", 
                    "Q(x)": "非齐次项"
                },
                "use_cases": ["人口增长模型", "RC电路分析", "放射性衰变"],
                "variations": ["y' + ay = b (常系数情况)"]
            },
            {
                "name": "拉普拉斯变换定义",
                "latex": "\\mathcal{L}\\{f(t)\\} = F(s) = \\int_0^\\infty f(t)e^{-st}dt",
                "variables": {
                    "F(s)": "拉普拉斯变换",
                    "f(t)": "原函数",
                    "s": "复变量"
                },
                "use_cases": ["求解微分方程", "系统分析", "信号处理"],
                "variations": ["逆变换: f(t) = L^{-1}{F(s)}"]
            }
        ],
        "examples": [
            {
                "concept": "一阶微分方程求解",
                "problem": "求解微分方程 dy/dx - 2y = e^x，初条件 y(0) = 1",
                "solution_steps": [
                    "识别为一阶线性微分方程，P(x) = -2, Q(x) = e^x",
                    "计算积分因子 μ(x) = e^(-2x)",
                    "方程两边乘以积分因子: e^(-2x)dy/dx - 2e^(-2x)y = e^(-x)",
                    "左边为 d/dx[ye^(-2x)] = e^(-x)",
                    "积分得 ye^(-2x) = -e^(-x) + C",
                    "通解: y = -e^x + Ce^(2x)",
                    "代入初条件: 1 = -1 + C，得 C = 2",
                    "特解: y = 2e^(2x) - e^x"
                ],
                "key_insight": "积分因子法是求解一阶线性微分方程的标准方法",
                "common_mistakes": ["忘记计算积分因子", "积分常数处理错误", "初条件代入错误"]
            },
            {
                "concept": "拉普拉斯变换应用",
                "problem": "用拉普拉斯变换求解 y'' + 4y = 8, y(0) = 0, y'(0) = 2",
                "solution_steps": [
                    "对方程两边取拉普拉斯变换",
                    "L{y''} + 4L{y} = L{8}",
                    "s²Y(s) - sy(0) - y'(0) + 4Y(s) = 8/s",
                    "代入初条件: s²Y(s) - 2 + 4Y(s) = 8/s",
                    "(s² + 4)Y(s) = 8/s + 2",
                    "Y(s) = (8 + 2s)/(s(s² + 4))",
                    "部分分式分解: Y(s) = 2/s + 2s/(s² + 4)",
                    "逆变换: y(t) = 2 + 2cos(2t)"
                ],
                "key_insight": "拉普拉斯变换将微分方程转化为代数方程，简化求解",
                "common_mistakes": ["初条件处理错误", "部分分式分解错误", "逆变换查表错误"]
            }
        ],
        "practical_tips": [
            "先判断微分方程的类型和阶数",
            "一阶线性优先考虑积分因子法",
            "高阶常系数用特征方程法",
            "复杂方程考虑拉普拉斯变换",
            "验算时将解代入原方程检验"
        ],
        "metadata": {
            "generation_method": "sample_data",
            "focus": "problem_solving",
            "difficulty_level": "undergraduate"
        },
        "processing_info": {
            "success": True,
            "method": "demo_mode",
            "quality": "sample"
        }
    }


@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """获取处理状态"""
    
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    job = processing_jobs[job_id]
    return JSONResponse({
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "message": job["message"],
        "filename": job["filename"]
    })


@app.get("/notes/{job_id}", response_class=HTMLResponse)
async def view_notes(job_id: str, request: Request):
    """查看生成的笔记"""
    
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    job = processing_jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="笔记尚未生成完成")
    
    notes_data = job["result"]["notes_data"]
    
    return templates.TemplateResponse("notes_view.html", {
        "request": request,
        "job_id": job_id,
        "notes": notes_data,
        "title": notes_data.get("title", "学习笔记")
    })


@app.get("/download/{job_id}")
async def download_notes(job_id: str, format: str = "json"):
    """下载笔记文件"""
    
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    job = processing_jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="笔记尚未生成完成")
    
    result = job["result"]
    
    if format == "json" and result["json_path"]:
        return FileResponse(
            result["json_path"],
            filename=f"{result['title']}.json",
            media_type="application/json"
        )
    elif format == "html" and result["html_path"]:
        return FileResponse(
            result["html_path"], 
            filename=f"{result['title']}.html",
            media_type="text/html"
        )
    else:
        raise HTTPException(status_code=404, detail="文件不存在")


@app.get("/api/notes/{job_id}")
async def get_notes_api(job_id: str):
    """API接口获取笔记JSON数据"""
    
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    job = processing_jobs[job_id]
    
    if job["status"] != "completed":
        return JSONResponse({
            "status": job["status"],
            "message": job["message"],
            "progress": job["progress"]
        })
    
    return JSONResponse(job["result"]["notes_data"])


@app.get("/jobs")
async def list_jobs():
    """列出所有处理任务"""
    
    jobs = []
    for job_id, job in processing_jobs.items():
        jobs.append({
            "job_id": job_id,
            "filename": job["filename"],
            "status": job["status"],
            "progress": job["progress"],
            "created_at": job["created_at"],
            "title": job["result"]["title"] if job["status"] == "completed" else None
        })
    
    # 按创建时间倒序排列
    jobs.sort(key=lambda x: x["created_at"], reverse=True)
    
    return JSONResponse({"jobs": jobs})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)