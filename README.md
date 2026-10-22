# exam-paper-generator

> 根据历年真题风格 + 章节重点，自动生成练习题并输出 PDF。支持公式渲染、多题型、多格式导出。

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 功能特点

- 📄 **真题解析** — 读取 PDF/DOCX 历年真题，自动分析出题风格
- 🧠 **AI 出题** — 基于真题风格 + 章节重点生成新题
- 🔢 **多题型支持** — 选择题、填空题、判断题、解答题
- 🧮 **公式渲染** — KaTeX 渲染 LaTeX 公式（电极电位、浓度计算、光谱分析等）
- 📑 **PDF 输出** — 直接生成 A4 排版的 PDF 试卷
- 🔍 **题库去重** — 生成的题目与原题不重复，保证练习价值

## 支持的输入格式

| 格式 | 说明 |
|------|------|
| PDF | 文字型或图片扫描型（自动 OCR） |
| DOCX | Word 文档 |
| 纯文本 | TXT/Markdown |

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/242742532Celestia/exam-paper-generator.git
cd exam-paper-generator
```

### 2. 安装依赖

```bash
pip install pdfplumber python-docx playwright
playwright install chromium
# 或 tesseract（用于图片 PDF OCR）
sudo apt install tesseract-ocr tesseract-ocr-chi-sim  # Linux
brew install tesseract tesseract-lang                   # macOS
```

### 3. 准备输入文件

将历年真题 PDF/DOCX 和章节重点笔记放到同一目录，例如：

```
my_exam/
├── 仪器分析-真题1.pdf
├── 仪器分析-真题2.docx
└── 章节重点.md
```

### 4. 生成练习题

```bash
# 提取真题文本
python3 scripts/extract_text.py my_exam/真题1.pdf my_exam/真题2.docx

# 生成 Markdown 试卷（调用 LLM，填写你的 API key）
python3 scripts/generate_paper.py \
  --source "历年真题文本内容..." \
  --focus "章节重点..." \
  --subject "仪器分析" \
  --output my_paper.md

# 渲染为 PDF
python3 scripts/build_pdf.py my_paper.md output.pdf
```

### 5. 一键运行（Python API）

```python
from scripts.build_pdf import build_pdf
from scripts.extract_text import extract_file

# 1. 提取文本
text = extract_file("真题.pdf")

# 2. 调用 LLM 生成题目（参考 SKILL.md 中的 Prompt 设计）
# ...

# 3. 渲染 PDF
build_pdf("试卷.md", "试卷.pdf")
```

## 项目结构

```
exam-paper-generator/
├── SKILL.md                  # Mavis Skill 定义（触发词、流程、设计思路）
├── scripts/
│   ├── extract_text.py       # PDF/DOCX 文本提取 + OCR
│   ├── build_pdf.py          # Markdown → PDF（含 KaTeX 公式渲染）
│   └── generate_paper.py     # AI 出题核心逻辑（需配合 LLM API）
├── README.md
├── SKILL.md
├── LICENSE
├── .gitignore
└── .github/workflows/test.yml # CI 冒烟测试
```

## 设计思路

详见 `SKILL.md` — 包含完整的 Prompt 设计、题型分布策略、公式处理方案。

## 与同类项目对比

| 功能 | exam-paper-generator | Quizbot | Questgen | Qujini |
|------|:------------------:|:-------:|:--------:|:------:|
| PDF/DOCX 解析 | ✅ | ✅ | ✅ | ❌ |
| AI 生成新题 | ✅ | ✅ | ✅ | ❌ |
| 多题型（选填判解） | ✅ | ✅ | ✅ | ✅ |
| **公式渲染（KaTeX）** | ✅ | ❌ | ❌ | ❌ |
| **章节重点导向** | ✅ | ❌ | ❌ | ❌ |
| **历史真题蓝本** | ✅ | ❌ | ❌ | ❌ |
| 开源 | ✅ | ❌ | ❌ | ✅ |

## License

MIT — 欢迎 star、fork、提 PR！
