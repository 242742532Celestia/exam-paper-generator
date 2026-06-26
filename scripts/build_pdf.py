#!/usr/bin/env python3
"""
将 Markdown（含 LaTeX 公式）转换为 PDF。
使用 Playwright + KaTeX CDN，支持行内/块级数学公式。

用法:
  python3 build_pdf.py <input.md> <output.pdf>
  python3 build_pdf.py <input.md>              # 输出到同名 .pdf

依赖:
  pip install playwright && playwright install chromium
  (playwright 已安装在 /root/.cache/ms-playwright/)
"""
import sys
import re
import os
from pathlib import Path

# ─── 数学符号归一化 ────────────────────────────────────────────────

GREEK_MAP = {
    'Α': 'Alpha', 'α': 'alpha', 'Β': 'Beta', 'β': 'beta',
    'Γ': 'Gamma', 'γ': 'gamma', 'Δ': 'Delta', 'δ': 'delta',
    'Ε': 'Epsilon', 'ε': 'epsilon', 'Ζ': 'Zeta', 'ζ': 'zeta',
    'Η': 'Eta', 'η': 'eta', 'Θ': 'Theta', 'θ': 'theta',
    'Ι': 'Iota', 'ι': 'iota', 'Κ': 'Kappa', 'κ': 'kappa',
    'Λ': 'Lambda', 'λ': 'lambda', 'Μ': 'Mu', 'μ': 'mu',
    'Ν': 'Nu', 'ν': 'nu', 'Ξ': 'Xi', 'ξ': 'xi',
    'Ο': 'Omicron', 'ο': 'omicron', 'Π': 'Pi', 'π': 'pi',
    'Ρ': 'Rho', 'ρ': 'rho', 'Σ': 'Sigma', 'σ': 'sigma',
    'Τ': 'Tau', 'τ': 'tau', 'Υ': 'Upsilon', 'υ': 'upsilon',
    'Φ': 'Phi', 'φ': 'phi', 'Χ': 'Chi', 'χ': 'chi',
    'Ψ': 'Psi', 'ψ': 'psi', 'Ω': 'Omega', 'ω': 'omega',
}

GREEK_PATTERN = re.compile(
    r'Α|α|Β|β|Γ|γ|Δ|δ|Ε|ε|Ζ|ζ|Η|η|Θ|θ|Ι|ι|Κ|κ|Λ|λ|Μ|μ|Ν|ν|Ξ|ξ|Ο|ο|Π|π|Ρ|ρ|Σ|σ|Τ|τ|Υ|υ|Φ|φ|Χ|χ|Ψ|ψ|Ω|ω'
)


def consume_subsup(text: str, i: int) -> int:
    """从 text[i] 开始消耗下标或上标，返回消耗的字符数（0=不匹配）。"""
    n = len(text)
    if i >= n or text[i] not in '_^':
        return 0
    j = i + 1
    if j >= n:
        return 0
    if text[j] == '{':
        k = j + 1
        brace = 1
        while k < n and brace > 0:
            if text[k] == '{':
                brace += 1
            elif text[k] == '}':
                brace -= 1
            k += 1
        return k - i
    # ^-N / ^+N
    if text[j] in '+-' and j + 1 < n and text[j + 1].isdigit():
        k = j + 2
        while k < n and text[k].isdigit():
            k += 1
        return k - i
    # ^( ... )
    if text[j] == '(':
        k = j + 1
        while k < n and text[k] != ')':
            k += 1
        if k < n:
            return k + 1 - i
    # ^数字、^分数
    if text[j].isdigit():
        k = j
        while k < n and (text[k].isdigit() or text[k] in '/.'):
            k += 1
        return k - i
    # ASCII word token
    if re.match(r'[A-Za-zΑ-Ωα-ω0-9]', text[j]):
        k = j
        while k < n and re.match(r'[A-Za-zΑ-Ωα-ω0-9]', text[k]):
            k += 1
        return k - i
    # 单个中文字符（避免吃中文描述）
    if re.match(r'[\u4e00-\u9fff]', text[j]):
        return 2
    return 0


def find_end_of_math(text: str, start: int) -> int:
    """从 start 找数学段末尾位置（ASCII word token + 上下标链）。"""
    n = len(text)
    i = start
    while i < n:
        ch = text[i]
        # ASCII 字母数字希腊字母 → 属于数学段
        if re.match(r'[A-Za-zΑ-Ωα-ω0-9]', ch):
            i += 1
            while i < n and re.match(r'[A-Za-zΑ-Ωα-ω0-9]', text[i]):
                i += 1
            continue
        # 上下标 → 消耗后继续（不认识的后缀如 ^pot 也跳过，保持 math 段连续）
        if ch in '_^':
            delta = consume_subsup(text, i)
            if delta:
                i += delta
                continue
            # ^pot / _pot 这类后缀，跳过 ^/_ 本身继续
            i += 1
            continue
        # 括号、加减乘除等常见数学字符 → 继续
        if ch in '()[]{}+-*/=<>≤≥≠≈≡×÷·,.·':
            i += 1
            continue
        # 空格、汉字、标点 → 退出
        break
    return i


def greek_to_latex(text: str) -> str:
    """将希腊字母转为 LaTeX 命令。"""
    def repl(m):
        return GREEK_MAP.get(m.group(), m.group())
    return GREEK_PATTERN.sub(repl, text)


def normalize_math(text: str) -> str:
    """
    将 Markdown 中的纯文本数学符号转为 LaTeX 块。
    规则：
      - 已被 $...$ 或 $$...$$ 包裹的跳过
      - 检测裸露的数学符号序列（ASCII word + 可选上下标），
        转为 $...$，内部希腊字母转 LaTeX 命令
    """
    # 先把已有的 $...$ 临时占位
    PLACEHOLDER = '\x00MATH{:03d}MATH\x00'
    math_blocks = {}
    def save_block(m):
        idx = len(math_blocks)
        math_blocks[idx] = m.group()
        return PLACEHOLDER.format(idx)
    # 双重转义 $（已有 $...$ 或 $$...$$）
    protected = re.sub(r'\$\$.*?\$\$', save_block, text, flags=re.DOTALL)
    protected = re.sub(r'(?<!\\)\$[^$\n]+?(?<!\\)\$', save_block, protected)

    # 扫描裸露的数学序列
    result = []
    i = 0
    n = len(protected)
    while i < n:
        ch = protected[i]
        # ASCII word → 可能是数学
        if re.match(r'[A-Za-zΑ-Ωα-ω0-9]', ch):
            j = i
            # 吃连续 ASCII word
            while j < n and re.match(r'[A-Za-zΑ-Ωα-ω0-9]', protected[j]):
                j += 1
            token = protected[i:j]
            # 后面跟上下标？
            k = j
            while True:
                delta = consume_subsup(protected, k)
                if delta:
                    k += delta
                else:
                    break
            math_content = protected[i:k].strip()
            # 只有2个字符以上才转换（避免单个字母误判）
            if len(math_content) > 1:
                latex = greek_to_latex(math_content)
                # _外 / _内 结构处理
                def wrap_text(m):
                    inner = m.group(1)
                    return r'_{\text{' + inner.lstrip('{').rstrip('}') + r'}}'
                latex = re.sub(r'_([A-Za-zΑ-Ωα-ω0-9]+)', r'_{\1}', latex)
                latex = re.sub(r'_(\{[^}]+\})', wrap_text, latex)
                # 上下标里的 ^N / ^-N / ^(...)
                latex = re.sub(r'\^(-?\d+)', r'^{\1}', latex)
                latex = re.sub(r'\^\{(\d+)/(\d+)\}', r'^{\frac{\1}{\2}}', latex)
                latex = re.sub(r'^\^', r'^{', latex)  # 孤立 ^
                result.append(f'${latex}$')
                i = k
                continue
            else:
                result.append(protected[i])
                i = j
            continue
        result.append(protected[i])
        i += 1

    out = ''.join(result)
    # 后处理：^(数字/数字) → ^{\frac{数字}{数字}}
    out = re.sub(r'\^\(([^)]+)\)', lambda m: '^{\\frac{' + m.group(1).replace('/', '}{') + '}}', out)
    # 恢复被占位的块
    for idx, block in math_blocks.items():
        out = out.replace(PLACEHOLDER.format(idx), block)
    return out


# ─── Markdown → HTML 转换 ───────────────────────────────────────────

KATEX_CDN = (
    '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">\n'
    '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>\n'
    '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"'
    ' onload="renderMathInElement(document.body,{delimiters:[{left:\'$\',right:\'$\',display:false},'
    '{left:\'$$\',right:\'$$\',display:true}],trust:true,strict:false});"></script>\n'
)

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "Source Han Sans SC", "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif; }
"""


def md_to_html(md_text: str) -> str:
    lines = md_text.split('\n')
    out = []
    i = 0
    in_table = False
    table_rows = []

    def flush_table(rows, out):
        if not rows:
            return
        if len(rows) >= 2:
            headers = [c.strip() for c in rows[0].strip('|').split('|')]
            out.append('<thead><tr>' + ''.join(f'<th>{h}</th>' for h in headers) + '</tr></thead>')
            out.append('<tbody>')
            for r in rows[2:]:
                cells = [c.strip() for c in r.strip('|').split('|')]
                cells = [re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', c) for c in cells]
                out.append('<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>')
            out.append('</tbody>')
        out.append('</table>')

    while i < len(lines):
        line = lines[i]

        # 表格行
        if line.startswith('|') and '|' in line[1:]:
            table_rows.append(line)
            i += 1
            continue
        else:
            if table_rows:
                flush_table(table_rows, out)
                table_rows = []
                in_table = False

        # 标题
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            level = len(m.group(1))
            out.append(f'<h{level}>{m.group(2)}</h{level}>')
            i += 1
            continue

        # 分隔线
        if re.match(r'^---+$', line):
            out.append('<hr>')
            i += 1
            continue

        # 代码块
        if line.startswith('```'):
            lang = line[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(lines[i])
                i += 1
            code = '\n'.join(code_lines)
            if lang:
                out.append(f'<pre><code class="language-{lang}">{code}</code></pre>')
            else:
                out.append(f'<pre><code>{code}</code></pre>')
            i += 1
            continue

        # 行内代码
        line = re.sub(r'`([^`]+)`', r'<code>\1</code>', line)

        # 粗体和斜体
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)

        # 无序列表
        _bullet_re = re.compile(r'^[-*+]\s+')
        if _bullet_re.match(line):
            _bullet_txt = _bullet_re.sub('', line)
            out.append(f'<li>{_bullet_txt}</li>')
            i += 1
            continue

        # 有序列表
        m = re.match(r'^\d+\.\s+(.*)', line)
        if m:
            out.append(f'<li>{m.group(1)}</li>')
            i += 1
            continue

        # 引用块
        if line.startswith('>'):
            out.append(f'<blockquote>{line[1:].strip()}</blockquote>')
            i += 1
            continue

        # 解析题答案行：**答案：X**
        if re.search(r'\*\*答案', line):
            out.append(f'<p class="answer">{line}</p>')
            i += 1
            continue

        # 解析行：**解析：**
        if re.search(r'\*\*解析', line):
            out.append(f'<p class="解析">{line}</p>')
            i += 1
            continue

        # 空行
        if not line.strip():
            out.append('<br>')
            i += 1
            continue

        # 普通段落
        out.append(f'<p>{line}</p>')
        i += 1

    # 表格收尾
    if table_rows:
        flush_table(table_rows, out)

    body = '\n'.join(out)
    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
{CSS}
</style>
{KATEX_CDN}
</head>
<body>
{body}
</body>
</html>"""


def build_pdf(input_md: str, output_pdf: str, timeout_ms: int = 60000) -> None:
    """用 Playwright 将 Markdown 文件转为 PDF。"""
    from playwright.sync_api import sync_playwright

    input_path = Path(input_md)
    md_text = input_path.read_text(encoding='utf-8')
    md_text = normalize_math(md_text)
    html = md_to_html(md_text)

    # 写临时 HTML
    tmp_html = input_path.with_suffix('.tmp.html')
    tmp_html.write_text(html, encoding='utf-8')

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path='/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome'
        )
        page = browser.new_page()
        page.goto(f'file://{tmp_html.absolute()}', wait_until='networkidle', timeout=timeout_ms)
        # 等 KaTeX 渲染
        page.wait_for_timeout(3000)
        page.pdf(
            path=output_pdf,
            format='A4',
            margin={'top': '20mm', 'bottom': '20mm', 'left': '15mm', 'right': '15mm'},
            print_background=True,
            display_header_footer=False,
        )
        browser.close()

    tmp_html.unlink(missing_ok=True)


def main():
    if len(sys.argv) < 2:
        print("用法: python3 build_pdf.py <input.md> [output.pdf]", file=sys.stderr)
        sys.exit(1)
    input_md = sys.argv[1]
    if len(sys.argv) >= 3:
        output_pdf = sys.argv[2]
    else:
        output_pdf = str(Path(input_md).with_suffix('.pdf'))
    build_pdf(input_md, output_pdf)
    print(f"PDF: {output_pdf}")


if __name__ == "__main__":
    main()
