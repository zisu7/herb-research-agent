# herb‑research‑agent｜中药天然产物研发智能体

> 📌 中医药垂直领域开源AI项目｜中药研发专项工程｜仅供学习科研参考，不构成医疗建议

## 📖 项目简介
本项目为中药天然产物研发专项工程，聚焦中药科研方向，提供 828 味本地药材库的检索统计能力，
并内置四个研发工作台，覆盖经典名方调研、适应症复方挖掘、复方前置安全评估、药材资源替代筛选。

本工程由 `herb-llm-agent` 双模块系统拆分而来，仅保留研发相关能力，不含任何药膳问诊业务。

## 🧩 两大模块
1. **中药天然产物研发模块（菜单 1‑5）**
   - 1. 浏览全部药材数据
   - 2. 药名关键词检索药材（支持本地检索 + AI 研发分析）
   - 3. 按中药类别筛选
   - 4. 按归经条件筛选药材
   - 5. 数据统计功能

2. **研发工作台专区（菜单 9‑12）**
   - 9. 工作台1：经典名方开发调研
   - 10. 工作台2：适应症候选复方挖掘
   - 11. 工作台3：复方药物警戒-前置安全评估
   - 12. 工作台4：药材资源评估与替代筛选

## 🚀 运行说明
### 环境准备
1. 安装项目依赖：`pip install -r requirements.txt`
2. 在项目根目录配置 `.env` 文件，填入 DeepSeek API Key：
   ```
   DEEPSEEK_API_KEY=sk-xxxxxxxx
   ```

### 启动
```
python main.py
```
主菜单输入对应数字进入功能：
- 1‑5：中药天然产物研发模块
- 9‑12：研发工作台（采集业务参数 → 调用智能体推理 → 输出 Markdown 调研简报，可选导出本地 txt）
- 0：退出系统

## 📂 项目目录说明

```
herb-research-agent
├─ main.py            # 主程序入口
├─ src/
│  ├─ main_run.py     # 主菜单与业务流程
│  ├─ agent_entry.py  # 智能体统一入口
│  ├─ data_loader.py  # 药材数据加载
│  ├─ agents/         # 工作台调度 + 智能体工具
│  │  ├─ agent_workbench.py  # 研发工作台调度脚本
│  │  └─ agent_utils.py      # 通用智能体调用
│  ├─ llm/            # LLM 客户端 + 研发 Agent
│  │  ├─ llm_client.py
│  │  └─ agent_research.py
│  ├─ data/           # 药材数据集（herb_raw.json）
│  ├─ utils/ database/ fsrs/  # 辅助工具模块
│  └─ ...
├─ prompts/           # 四份工作台 prompt 模板
│  ├─ workbench1_prompt.md
│  ├─ workbench2_prompt.md
│  ├─ workbench3_prompt.md
│  └─ workbench4_prompt.md
├─ static/            # 药材知识库 json（828味）
├─ docs/              # 提示词模板
├─ tests/             # 测试脚本
├─ .env               # 密钥配置（自行新建，不上传git）
├─ .gitignore
├─ requirements.txt
└─ README.md
```

## ⚠️ 免责声明
本项目全部输出仅为中药研发前期智能辅助参考，**不可直接作为新药研发、用药或审批的最终判定依据**。
- 适应症匹配、复方作用通路推演、药材替代等效推断等属 AI 推演，须由中药/药学研发人员研判，并经药理、制剂与临床试验验证。
- AI 不能替代药理实验、动物试验、临床试验，不具备法定审评结论效力。
