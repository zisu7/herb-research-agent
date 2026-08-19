import re
import sys
from pathlib import Path
from datetime import datetime

# 解析项目根目录：src/agents/agent_workbench.py → 上三级
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.agents.agent_utils import run_agent
from src.llm.llm_client import is_llm_available

PROMPTS_DIR = _PROJECT_ROOT / "prompts"

# 工作台注册表：编号 → 名称、prompt 文件、参数收集规则
WORKBENCH_REGISTRY = {
    1: {
        "name": "经典名方开发调研工作台",
        "prompt_file": "workbench1_prompt.md",
        "params": [
            {"key": "research_direction", "label": "调研方向/关注领域", "hint": "如：补气安神、清热解毒、妇科调理"},
            {"key": "reference_scope", "label": "参考范围", "hint": "如：《伤寒论》《金匮要略》或具体方名如四物汤"},
            {"key": "extra_note", "label": "补充说明（可空）", "hint": "如：限定药味≤6味、偏好药食同源"},
        ],
    },
    2: {
        "name": "适应症候选复方挖掘工作台",
        "prompt_file": "workbench2_prompt.md",
        "params": [
            {"key": "target_indication", "label": "目标适应症/症状", "hint": "如：失眠、消化不良、气虚乏力"},
            {"key": "screening_preference", "label": "筛选偏好", "hint": "如：药食同源优先、排除含毒性药材"},
            {"key": "extra_note", "label": "补充说明（可空）", "hint": "如：限定药味数、限定出处"},
        ],
    },
    3: {
        "name": "复方药物警戒-前置安全评估工作台",
        "prompt_file": "workbench3_prompt.md",
        "params": [
            {"key": "formula_composition", "label": "待评估复方组成", "hint": "如：人参、白术、茯苓、甘草"},
            {"key": "target_population", "label": "目标人群", "hint": "如：一般成人、孕妇、儿童、肝肾功能异常"},
            {"key": "extra_note", "label": "补充说明（可空）", "hint": "如：关注十八反、关注超量风险"},
        ],
    },
    4: {
        "name": "药材资源评估与替代筛选工作台",
        "prompt_file": "workbench4_prompt.md",
        "params": [
            {"key": "target_herb", "label": "目标药材名称", "hint": "如：人参、天然牛黄、麝香"},
            {"key": "substitute_reason", "label": "替代原因", "hint": "如：资源稀缺、价格高、毒性、过敏"},
            {"key": "usage_scenario", "label": "使用场景", "hint": "如：药膳、代茶饮、研发制剂"},
            {"key": "extra_note", "label": "补充说明（可空）", "hint": "如：限定药食同源、限定产地"},
        ],
    },
}

# 专属提示禁用区标记（与 prompt 文件中的标记一致）
_DISABLED_START = "WORKBENCH_SPECIFIC_DISABLED_START"
_DISABLED_END = "WORKBENCH_SPECIFIC_DISABLED_END"


def _strip_disabled_section(prompt_text: str) -> str:
    """剥离 prompt 模板中暂未启用的「工作台专属提示」区块，使其不参与推理。"""
    pattern = re.compile(
        r"<!--===\s*" + _DISABLED_START + r"\s*===.*?" + _DISABLED_END + r"\s*===-->",
        re.DOTALL,
    )
    return pattern.sub("", prompt_text)


def load_prompt(workbench_id: int) -> str:
    """根据工作台编号加载对应 prompt 模板，并剥离暂未启用的专属提示区块。"""
    if workbench_id not in WORKBENCH_REGISTRY:
        raise ValueError(f"未知工作台编号：{workbench_id}")
    cfg = WORKBENCH_REGISTRY[workbench_id]
    path = PROMPTS_DIR / cfg["prompt_file"]
    if not path.exists():
        raise FileNotFoundError(f"提示词模板文件不存在：{path}")
    raw = path.read_text(encoding="utf-8")
    return _strip_disabled_section(raw)


def collect_params(workbench_id: int, input_fn=input) -> dict:
    """交互式收集用户业务参数。input_fn 可注入以便测试。"""
    if workbench_id not in WORKBENCH_REGISTRY:
        raise ValueError(f"未知工作台编号：{workbench_id}")
    cfg = WORKBENCH_REGISTRY[workbench_id]
    params = {}
    print(f"\n【{cfg['name']}】参数采集")
    for p in cfg["params"]:
        prompt_str = f"请输入{p['label']}"
        if p.get("hint"):
            prompt_str += f"（{p['hint']}）"
        val = input_fn(f"{prompt_str}: ").strip()
        params[p["key"]] = val if val else "未提供"
    return params


def build_user_message(workbench_id: int, params: dict) -> str:
    """根据工作台编号与参数构造提交给智能体的用户消息。"""
    cfg = WORKBENCH_REGISTRY[workbench_id]
    lines = [f"【工作台】{cfg['name']}", "【用户业务参数】"]
    for p in cfg["params"]:
        lines.append(f"- {p['label']}: {params.get(p['key'], '未提供')}")
    lines.append("")
    lines.append("请严格按提示词模板规定的 Markdown 章节输出调研简报，文字精简，全文控制在 1000 字以内。")
    return "\n".join(lines)


def run_workbench(workbench_id: int, params: dict = None) -> str:
    """
    工作台调度入口：加载 prompt 模板 → 构造用户消息 → 调用现有智能体推理 → 返回 Markdown 报告。
    params 为空时进入交互式参数采集。
    """
    if not is_llm_available():
        raise RuntimeError("DEEPSEEK_API_KEY 未配置，工作台智能体不可用。请在 .env 中配置有效 API Key。")
    if workbench_id not in WORKBENCH_REGISTRY:
        raise ValueError(f"未知工作台编号：{workbench_id}")
    if params is None:
        params = collect_params(workbench_id)
    system_prompt = load_prompt(workbench_id)
    user_msg = build_user_message(workbench_id, params)
    report = run_agent(system_prompt, user_msg)
    return report


def export_workbench_report(workbench_id: int, params: dict, report: str, save_dir=None) -> str:
    """
    将工作台报告导出为本地 txt 文件，沿用现有问诊记录保存方案（records/ + 时间戳）。
    返回：保存文件绝对路径；失败返回以“导出失败：”开头的说明字符串。
    """
    try:
        if save_dir is None:
            save_dir = _PROJECT_ROOT / "records"
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cfg = WORKBENCH_REGISTRY[workbench_id]
        safe_name = cfg["name"].replace("-", "")
        filepath = save_dir / f"工作台{workbench_id}_{safe_name}_{timestamp}.txt"

        lines = []
        lines.append("=" * 60)
        lines.append(f"研发工作台{workbench_id}：{cfg['name']}")
        lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        lines.append("\n【用户业务参数】")
        for p in cfg["params"]:
            lines.append(f"- {p['label']}: {params.get(p['key'], '')}")
        lines.append("\n【调研简报】")
        lines.append(report)
        lines.append("\n" + "=" * 60)
        lines.append("免责声明：本报告仅为研发前期智能辅助参考，不可作为最终判定依据。")
        lines.append("=" * 60)

        filepath.write_text("\n".join(lines), encoding="utf-8")
        return str(filepath)
    except Exception as e:
        return f"导出失败：{e}"


def list_workbenches() -> dict:
    """返回工作台编号→名称映射，供主菜单展示。"""
    return {wid: cfg["name"] for wid, cfg in WORKBENCH_REGISTRY.items()}


if __name__ == "__main__":
    # 直接运行该脚本时，提供一个最小化调试入口
    print("研发工作台调度脚本（调试入口）")
    print("可选工作台：", list_workbenches())
    try:
        wid = int(input("请输入工作台编号(1-4): ").strip())
        report = run_workbench(wid)
        print("\n=====【工作台报告】=====")
        print(report)
        print("========================\n")
    except Exception as e:
        print(f"工作台运行失败：{e}")
