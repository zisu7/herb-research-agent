import re
import json
from src.llm.llm_client import chat_completion

def extract_json(raw_text: str) -> str:
    """清洗LLM返回，剥离```json代码块标记"""
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, raw_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return raw_text.strip()

def run_agent(system_prompt: str, user_input: str) -> str:
    """通用Agent调用入口，调用Deepseek接口"""
    resp = chat_completion(system_prompt=system_prompt, user_content=user_input)
    return resp
