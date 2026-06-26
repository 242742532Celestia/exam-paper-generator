---
name: exam-paper-generator
description: |
  根据上传的历年真题PDF/DOCX，仿照出题风格并结合用户总结的章节重点，
  生成新的练习题（含答案解析），输出为PDF格式。触发词包括"生成习题"、
  "生成练习题"、"根据真题生成练习"、"生成试卷"、"生成考题"、
  "出几道题"、"练习题"、"生成题库"。不用于创意写作或闲聊。
---

# Exam Paper Generator

根据历年真题风格 + 章节重点，自动生成练习题并输出 PDF。

## Inputs to collect

调用 skill 前必须确认：
- **历年真题**：至少1套上传（PDF或DOCX），包含题目和答案
- **章节重点/笔记**（可选但强烈推荐）：用户总结的各章要点，帮助生成有针对性的题目
- **科目名称**：用于试卷标题
- **生成套数**：默认生成 2 套练习（用户没说则默认2）
- **每套题目数量**：默认与真题相近（用户没说则默认 20–25 题选择题 + 10 填空 + 10 判断 + 4 解答）

## Procedure

### 1. 分析真题风格

用 `scripts/extract_text.py` 读取所有上传文件，提取：
- 题目数量和类型分布（选择/填空/判断/解答）
- 每种题型的题号格式和编号规律
- 答案的呈现方式（直接附在题后/单独在末尾）
- 高频知识点和常考概念
- 难度梯度（基础题/综合题比例）

### 2. 生成练习题 Markdown

每套试卷按以下结构生成 Markdown：

```
# [科目名称] 练习题 · 第X套

## 一、选择题（共XX题，每题X分）

1. [题干，含公式用 LaTeX 如 $E = E^0 + \frac{RT}{nF}\ln\frac{a_{Ox}}{a_{Red}}$]
   A. [选项A]    B. [选项B]    C. [选项C]    D. [选项D]
   **答案：D**
   **解析：[分析为什么选D，引用章节重点中的相关知识点]**

## 二、填空题（共XX题）

1. [题目，含公式用 $...$]
   **答案：[填空内容]**
   **解析：[...]
```

**生成规则**：
- 选择题：4选项，答案分布均匀（ABCD各约1/4），正确答案位置随机
- 填空题：答案精确，常见考点：化学式、仪器参数、计算公式
- 判断题：正确/错误比例约1:1
- 解答题：覆盖综合应用、计算、原理分析
- **公式**：用 `$...$` 行内公式 或 `$$...$$` 块级公式，与真题格式一致
- **章节重点优先**：优先从用户上传的章节重点中提取考点来命题
- 避免与真题完全重复的题目，但保持同等的难度和覆盖面

### 3. 渲染公式

对 Markdown 中的公式做预处理（调用 `scripts/build_pdf.py` 中的 `normalize_math()` 函数），将纯文本数学符号转换为 LaTeX：

```
E_ISE  →  $E_{\text{ISE}}$     （电极符号下标）
E^0    →  $E^{0}$               （标准电位上标）
10^-5  →  $10^{-5}$             （指数格式）
D^(1/2) → $D^{\frac{1}{2}}$     （分数指数）
α      →  $\alpha$               （希腊字母）
λ_max  →  $\lambda_{\max}$       （下标带英文）
```

### 4. 生成 PDF

调用 `scripts/build_pdf.py` 将 Markdown 转换为 PDF：
```bash
python3 scripts/build_pdf.py input.md output.pdf
```

`build_pdf.py` 使用 Playwright（chromium）渲染，集成 KaTeX CDN 支持 LaTeX 公式显示。

### 5. 打包交付

- 每套练习生成独立的 PDF 文件
- 可选：将所有 PDF 打包为 `.zip`
- 交付给用户

## Output contract

- 每套练习题一个 PDF 文件
- 每套包含：**试卷正文**（题目）+ **参考答案与解析**（紧随题目后）
- 文件命名：`[科目名]-[套序]练习题.pdf`
- 公式渲染正确（上下标、分数、希腊字母）

## Failure handling

| 失败场景 | 处理方式 |
|---------|---------|
| 上传文件全是图片型PDF（无法文字提取） | 使用 `pdf2image` + `pytesseract` 做 OCR；告知用户 OCR 可能有个别识别误差 |
| DOCX 读取失败 | 回退：用 `pandoc` 转为文本再提取 |
| Playwright 生成 PDF 失败 | 检查 chromium 路径是否正确；备用：用 `weasyprint`（如已安装）或回退到纯文本 PDF |
| 公式渲染乱码 | 确保 `normalize_math()` 生效；CDN 需联网；备用方案降级为纯文本（无公式渲染） |
| 用户上传文件格式混乱 | 优先处理有明确答案的真题；告知用户哪些文件无法解析 |

## Scripts

### `scripts/extract_text.py`
读取 PDF（`pdfplumber`）和 DOCX（`python-docx`），统一返回纯文本字符串。
用法：`python3 scripts/extract_text.py <file_path>`

### `scripts/build_pdf.py`
将 Markdown（含 LaTeX 公式）转换为 PDF。使用 Playwright + KaTeX CDN。
用法：`python3 scripts/build_pdf.py <input.md> <output.pdf>`

---

## Examples

**Input**：用户上传了3套西南大学仪器分析历年真题（PDF）和一份各章重点笔记（DOCX），说"生成2套练习题"

**Output**：
- `仪器分析-练习题1.pdf` — 20选择 + 10填空 + 10判断 + 4解答，含完整解析
- `仪器分析-练习题2.pdf` — 同等规模，含完整解析
- `仪器分析-练习题.zip` — 打包下载

**Trigger style**：用户说"根据真题生成练习"、"帮我出几道题"、"生成习题"
