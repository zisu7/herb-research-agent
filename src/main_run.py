import sys
import os
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.data_loader import load_tcm_herbs
from src.agent_entry import research_query, is_llm_available
from src.agents.agent_workbench import (
    run_workbench,
    export_workbench_report,
    collect_params as collect_workbench_params,
    list_workbenches,
)


def safe_input(prompt=""):
    try:
        return input(prompt)
    except EOFError:
        return "0"


def safe_input_int(prompt="", min_val=None, max_val=None):
    while True:
        try:
            val = safe_input(prompt).strip()
            if not val:
                if min_val is not None:
                    return min_val
                continue
            num = int(val)
            if min_val is not None and num < min_val:
                print(f"请输入 {min_val}-{max_val} 之间的数字")
                continue
            if max_val is not None and num > max_val:
                print(f"请输入 {min_val}-{max_val} 之间的数字")
                continue
            return num
        except ValueError:
            print("输入错误，请输入有效数字")


def display_herbs(herbs_list):
    if not herbs_list:
        print("\n暂无药材数据")
        return
    print(f"\n共找到 {len(herbs_list)} 味药材:")
    print("-" * 100)
    print(f"{'序号':<4} {'名称':<8} {'类别':<10} {'归经':<12} {'功效':<25} {'主要成分':<20} {'用量'}")
    print("-" * 100)
    for i, h in enumerate(herbs_list, 1):
        print(f"{i:<4} {h['name']:<8} {h['category']:<10} {h['meridian']:<12} {h['effect']:<25} {h['component']:<20} {h['dosage']}")
    print("-" * 100)




def _run_workbench_flow(workbench_id: int):
    """研发工作台统一流程：采集参数 → 调用智能体 → 打印简报 → 可选导出本地记录。"""
    workbenches = list_workbenches()
    print(f"\n【研发工作台{workbench_id}：{workbenches[workbench_id]}】")
    print("=" * 60)
    print("系统将依次完成：")
    print("  ① 采集业务参数")
    print("  ② 加载对应 prompt 模板，调用现有智能体执行推理")
    print("  ③ 输出 Markdown 调研简报（可选导出本地 txt）")
    print("=" * 60)
    try:
        params = collect_workbench_params(workbench_id)
        print(f"\n正在调用智能体生成调研简报...")
        report = run_workbench(workbench_id, params)
        print(f"\n{'=' * 60}")
        print(f"【工作台{workbench_id} 调研简报】")
        print(f"{'=' * 60}")
        print(report)
        print(f"{'=' * 60}\n")
        export_choice = safe_input("是否需要将本次工作台简报导出为本地txt文件保存？【是/否】: ").strip()
        if export_choice in ("是", "y", "Y", "yes", "YES"):
            saved_path = export_workbench_report(workbench_id, params, report)
            if saved_path.startswith("导出失败"):
                print(f"⚠️ {saved_path}")
            else:
                print(f"✅ 工作台简报已保存至：{saved_path}")
        else:
            print("好的，本次简报不导出文件。")
        print("\n✅ 工作台流程已完成，即将返回主菜单")
    except Exception as e:
        print(f"\n⚠️ 工作台运行失败: {e}")
        print("请检查 DEEPSEEK_API_KEY 配置是否正确")


def main():
    herbs = load_tcm_herbs()
    categories = sorted(set(h["category"] for h in herbs))
    meridian_list = ["心", "肝", "脾", "肺", "肾", "胃", "大肠", "小肠", "胆", "膀胱", "三焦", "心包"]
    meridians = sorted(m for m in meridian_list if any(m in h["meridian"] for h in herbs))
    while True:
        print("\n========《基于LLM多智能体的中药天然产物研发+药膳智能养生辅助系统》========")
        print("----------【模块一：中药天然产物研发模块｜科研方向，模拟AI制药、天然产物研发】----------")
        print("1.浏览全部药材数据")
        print("2.药名关键词检索药材")
        print("3.按中药类别筛选")
        print("4.按归经条件筛选药材")
        print("5.数据统计功能")
        print("----------【模块二：研发工作台专区｜中药天然产物研发辅助】----------")
        print("9.工作台1：经典名方开发调研")
        print("10.工作台2：适应症候选复方挖掘")
        print("11.工作台3：复方药物警戒-前置安全评估")
        print("12.工作台4：药材资源评估与替代筛选")
        print("0.退出系统")
        try:
            choice = safe_input_int("请输入选择(0-12): ", 0, 12)
        except (ValueError, EOFError):
            print("\n输入错误，请输入数字0-12")
            safe_input("按回车继续...")
            continue
        if choice == 0:
            print("\n感谢使用，再见！")
            break
        elif choice == 1:
            display_herbs(herbs)
        elif choice == 2:
            keyword = safe_input("\n请输入药材名称或研发问题: ").strip()
            if not keyword:
                print("\n输入不能为空")
            else:
                print(f"\n正在检索「{keyword}」...")
                kw_lower = keyword.lower()
                local_matches = []
                for h in herbs:
                    haystack = f"{h.get('name', '')} {h.get('category', '')} {h.get('meridian', '')} {h.get('effect', '')} {h.get('component', '')}".lower()
                    if kw_lower in haystack:
                        local_matches.append(h)
                    elif any(seg.strip() and seg.strip() in haystack for seg in kw_lower.split()):
                        if h not in local_matches:
                            local_matches.append(h)
                if local_matches:
                    print(f"\n{'=' * 60}")
                    print(f"【本地检索】共找到 {len(local_matches)} 味匹配药材")
                    print(f"{'=' * 60}")
                    for i, r in enumerate(local_matches, 1):
                        print(f"  {i}. {r['name']} ({r['category']}) - {r['effect']}")
                        print(f"     归经: {r['meridian']} | 成分: {r['component']} | 用量: {r['dosage']}")
                    try:
                        if is_llm_available():
                            print(f"\n🔍 AI正在拓展天然产物研发资料...")
                            llm_result = research_query(keyword)
                            if llm_result.get("mode") == "llm" and llm_result.get("success"):
                                print(f"\n{'=' * 60}")
                                print(f"【AI研发分析】来源: {llm_result.get('source', 'deepseek-chat')}")
                                print(f"{'=' * 60}")
                                print(llm_result["answer"])
                            elif llm_result.get("error"):
                                print(f"\n⚠️ AI拓展失败: {llm_result['error']}")
                    except Exception:
                        pass
                    if not is_llm_available():
                        print(f"\n💡 配置 DEEPSEEK_API_KEY 后可启用 AI 研发拓展分析")
                else:
                    print(f"\n本地库未找到「{keyword}」，正在搜索扩展数据库...")
                    research_result = research_query(keyword)
                    if research_result.get("mode") == "llm" and research_result.get("success"):
                        print(f"\n{'=' * 60}")
                        print(f"【AI研发分析】来源: {research_result.get('source', 'deepseek-chat')}")
                        print(f"{'=' * 60}")
                        print(research_result["answer"])
                    elif research_result.get("mode") == "local" and research_result.get("success"):
                        print(f"\n{'=' * 60}")
                        print(f"【扩展库检索】(共找到 {len(research_result.get('results', []))} 味)")
                        print(f"{'=' * 60}")
                        print(research_result.get("answer", ""))
                        ext_results = research_result.get("results", [])
                        if ext_results:
                            for i, r in enumerate(ext_results, 1):
                                comp = r.get("component", "") or ", ".join(r.get("components", []))
                                print(f"  {i}. {r['name']} ({r['category']}) - {r['effect']}")
                                print(f"     成分: {comp} | 禁忌: {r.get('contraindication', '')}")
                        else:
                            print(f"\n未找到匹配的药材")
                    else:
                        print(f"\n检索失败: {research_result.get('error', '未知错误')}")
        elif choice == 3:
            print("\n中药类别列表:")
            for i, cat in enumerate(categories, 1):
                print(f"  {i}. {cat}")
            try:
                cat_idx = safe_input_int("请输入类别序号: ", 1, len(categories)) - 1
                if 0 <= cat_idx < len(categories):
                    selected_cat = categories[cat_idx]
                    results = [h for h in herbs if h["category"] == selected_cat]
                    display_herbs(results)
                else:
                    print("\n序号无效")
            except ValueError:
                print("\n输入错误")
        elif choice == 4:
            print("\n归经列表:")
            for i, mer in enumerate(meridians, 1):
                print(f"  {i}. {mer}")
            try:
                mer_idx = safe_input_int("请输入归经序号: ", 1, len(meridians)) - 1
                if 0 <= mer_idx < len(meridians):
                    selected_mer = meridians[mer_idx]
                    results = [h for h in herbs if selected_mer in h["meridian"]]
                    display_herbs(results)
                else:
                    print("\n序号无效")
            except ValueError:
                print("\n输入错误")
        elif choice == 5:
            print("\n【数据统计】")
            print(f"药材总数量: {len(herbs)} 味")
            print(f"\n各类药材计数:")
            for cat in categories:
                count = sum(1 for h in herbs if h["category"] == cat)
                print(f"  {cat}: {count}味")
        elif choice == 9:
            _run_workbench_flow(1)
        elif choice == 10:
            _run_workbench_flow(2)
        elif choice == 11:
            _run_workbench_flow(3)
        elif choice == 12:
            _run_workbench_flow(4)
        else:
            print("\n输入错误，请输入数字0-12")
        if choice != 0:
            safe_input("\n按回车继续...")


if __name__ == "__main__":
    main()
