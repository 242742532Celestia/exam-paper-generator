#!/usr/bin/env python3
"""
生成练习题 Markdown 文件（调用 LLM API）。

用法:
  python3 generate_paper.py --source <真题文本> --focus <章节重点> \\
      --subject <科目名> --sets <套数> --output <输出文件>

环境变量:
  OPENAI_API_KEY   — OpenAI API Key
  MINIMAX_API_KEY  — MiniMax API Key（备用）
  DASHSCOPE_API_KEY — 阿里通义千问（备用）
"""
import argparse
import os
import sys


SYSTEM_PROMPT = """你是一位高校出题专家，擅长根据历年真题风格和章节重点，
设计高质量的练习题。你生成的题目：
1. 严格仿照真题的出题风格和难度
2. 优先覆盖章节重点中的核心考点
3. 不与原题完全重复，但保持同等难度
4. 选择题选项分布均匀（ABCD各约1/4）
5. 解答题注重综合应用和分析能力

输出格式：纯 Markdown，不要任何解释。"""

EXAM_TEMPLATE = """## 一、选择题（共{choice_n}题，每题{choice_score}分）

{choices}

## 二、填空题（共{fill_n}题，每题{fill_score}分）

{fills}

## 三、判断题（共{judge_n}题，每题{judge_score}分）

{judges}

## 四、解答题（共{essay_n}题，每题{essay_score}分）

{essays}
"""

CHOICE_TEMPLATE = """{n}. {question}
   A. {A}    B. {B}    C. {C}    D. {D}
   **答案：{answer}**
   **解析：{analysis}**
"""

FILL_TEMPLATE = """{n}. {question}
   **答案：{answer}**
   **解析：{analysis}**
"""

 JUDGE_TEMPLATE = """{n}. {statement}
   **答案：{answer}（正确/错误）**
   **解析：{analysis}**
"""

ESSAY_TEMPLATE = """{n}. {question}
   **参考答案：{answer}**
   **解析：{analysis}**
"""


def generate_exam(source_text: str, focus_text: str, subject: str,
                  choice_n: int = 20, fill_n: int = 10,
                  judge_n: int = 10, essay_n: int = 4) -> str:
    """
    调用 LLM 生成练习题。
    目前为 Stub 实现——替换为你实际使用的 API。
    """
    # ── 在这里接入你的 LLM API ─────────────────────────────────
    # 推荐使用 OpenAI / MiniMax / 通义千问 / 智谱 GLM
    #
    # 示例（OpenAI）:
    #   from openai import OpenAI
    #   client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    #   response = client.chat.completions.create(
    #       model="gpt-4o",
    #       messages=[
    #           {"role": "system", "content": SYSTEM_PROMPT},
    #           {"role": "user", "content": f"真题风格：\n{source_text}\n\n章节重点：\n{focus_text}\n\n科目：{subject}"}
    #       ],
    #       temperature=0.7,
    #   )
    #   return response.choices[0].message.content
    #
    # 示例（通义千问）:
    #   import openai as qwen
    #   os.environ["DASHSCOPE_API_KEY"] = os.environ.get("DASHSCOPE_API_KEY", "")
    #   # 使用 openai.Completion.create 或 dashscope SDK
    #
    raise NotImplementedError(
        "请在 generate_paper.py 中接入你的 LLM API。\n"
        "推荐：OpenAI (OPENAI_API_KEY) / MiniMax (MINIMAX_API_KEY) / 通义千问 (DASHSCOPE_API_KEY)"
    )


def main():
    parser = argparse.ArgumentParser(description="生成练习题 Markdown")
    parser.add_argument("--source", required=True, help="历年真题文本")
    parser.add_argument("--focus", default="", help="章节重点文本")
    parser.add_argument("--subject", default="科目", help="科目名称")
    parser.add_argument("--sets", type=int, default=2, help="生成套数（默认2）")
    parser.add_argument("--output", default="练习题.md", help="输出文件")
    args = parser.parse_args()

    lines = [f"# {args.subject} 练习题\n"]
    for i in range(1, args.sets + 1):
        print(f"正在生成第 {i}/{args.sets} 套...")
        content = generate_exam(
            source_text=args.source,
            focus_text=args.focus,
            subject=args.subject,
        )
        lines.append(f"\n---\n\n## 第 {i} 套\n\n{content}")

    output = "\n".join(lines)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"✅ 已保存至 {args.output}")


if __name__ == "__main__":
    main()
