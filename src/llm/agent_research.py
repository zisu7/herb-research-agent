import json
import os
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_HERB_DATA_PATH = _PROJECT_ROOT / "src" / "data" / "herb_raw.json"
_PROMPT_PATH = _PROJECT_ROOT / "docs" / "prompt_templates.md"


def _load_herbs():
    if not _HERB_DATA_PATH.exists():
        return []
    with open(_HERB_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_system_prompt():
    if not _PROMPT_PATH.exists():
        return "你是一位专业的中药天然产物研发专家。"
    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    section_start = content.find("## 中药研发Agent")
    if section_start == -1:
        return "你是一位专业的中药天然产物研发专家。"
    code_start = content.find("```", section_start)
    if code_start == -1:
        return "你是一位专业的中药天然产物研发专家。"
    text_start = code_start + 3
    code_end = content.find("```", text_start)
    if code_end == -1:
        return "你是一位专业的中药天然产物研发专家。"
    return content[text_start:code_end].strip()


def _local_search(query, herbs):
    results = []
    query = query.strip()
    query_lower = query.lower()
    keywords = [query_lower]
    if " " in query_lower:
        keywords.extend([k.strip() for k in query_lower.split() if k.strip()])
    for herb in herbs:
        name = herb.get("name", "")
        effect = herb.get("effect", "")
        components = herb.get("components", [])
        if isinstance(components, list):
            components_text = " ".join(components)
        else:
            components_text = str(components)
        component_alt = herb.get("component", "")
        category = herb.get("category", "")
        meridian = herb.get("meridian", "")
        text = f"{name} {effect} {components_text} {component_alt} {category} {meridian}".lower()
        matched = any(kw in text for kw in keywords)
        if matched:
            results.append({
                "name": name,
                "category": category,
                "meridian": meridian,
                "effect": effect,
                "components": components if isinstance(components, list) else [str(components)],
                "component": component_alt if component_alt else components_text,
                "contraindication": herb.get("contraindication", ""),
                "dosage": herb.get("dosage", ""),
                "is_food_medicine": herb.get("is_food_medicine", False),
            })
    return results


def research_query(user_question):
    herbs = _load_herbs()
    if not herbs:
        return {
            "mode": "local",
            "success": False,
            "error": "药材数据库为空，请检查 herb_raw.json 文件",
            "results": [],
        }

    system_prompt = _load_system_prompt()

    try:
        from .llm_client import is_llm_available, chat_completion
        if is_llm_available():
            try:
                herb_context = []
                for h in herbs[:47]:
                    herb_context.append(
                        f"药材: {h['name']} | 类别: {h['category']} | 归经: {h['meridian']} | "
                        f"功效: {h['effect']} | 成分: {', '.join(h.get('components', []))} | "
                        f"禁忌: {h.get('contraindication', '')}"
                    )
                context_text = "\n".join(herb_context)
                enriched_user = (
                    f"用户提问: {user_question}\n\n"
                    f"已知药材数据库（共{len(herbs)}味）:\n{context_text}\n\n"
                    f"请基于以上数据进行专业分析，给出研发建议。"
                )
                response = chat_completion(system_prompt, enriched_user)
                return {
                    "mode": "llm",
                    "success": True,
                    "answer": response,
                    "source": "deepseek-chat",
                }
            except Exception as e:
                return {
                    "mode": "llm",
                    "success": False,
                    "error": f"LLM调用失败: {str(e)}，已切换到本地检索模式",
                    "results": _local_search(user_question, herbs),
                }
    except ImportError:
        pass

    local_results = _local_search(user_question, herbs)
    return {
        "mode": "local",
        "success": True,
        "answer": f"【本地检索模式】共找到 {len(local_results)} 味匹配药材：",
        "results": local_results,
        "tip": "配置 DEEPSEEK_API_KEY 后可启用 AI 研发分析模式",
    }