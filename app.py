"""
知识迁移桥梁 v3.1 — 外观全面优化版
- 设计令牌系统 + 深色/浅色模式
- 步骤条导航 + 侧边栏折叠 + Tab 切换
- 迁移对卡片化 + 评分增强 + 运行摘要面板
- 微交互动画 + 悬浮导出栏 + 状态指示器
"""
import json, os, re
from datetime import datetime
from typing import List, Dict, Any

import streamlit as st
from streamlit.components.v1 import html as st_html

from pipeline import KnowledgeBridge, clear_cache, cache_stats
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

# ── 常量 ──
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".history.json")
MAX_HISTORY = 20

TEMPLATES = [
    ("厨艺 → 机器学习", "厨艺", "机器学习", "经典入门类比"),
    ("汽车驾驶 → 经济学", "汽车驾驶", "经济学", "驾驶理解市场机制"),
    ("法律 → 经济学", "法律", "经济学", "法律框架看经济"),
    ("音乐 → 哲学", "音乐", "哲学", "音乐之美到哲学思辨"),
    ("足球 → 项目管理", "足球", "项目管理", "团队竞技到管理"),
    ("摄影 → 数据分析", "摄影", "数据分析", "构图到数据洞察"),
    ("围棋 → 商业战略", "围棋", "商业战略", "博弈到战略思维"),
    ("中医 → 系统思维", "中医", "系统思维", "整体观到系统论"),
]

# ── 持久化 ──
def save_history(record: dict):
    try:
        data = json.load(open(HISTORY_FILE, "r", encoding="utf-8")) if os.path.exists(HISTORY_FILE) else []
        data.insert(0, record)
        json.dump(data[:MAX_HISTORY], open(HISTORY_FILE, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
    except Exception: pass

def load_history() -> list:
    try:
        if os.path.exists(HISTORY_FILE): return json.load(open(HISTORY_FILE, "r", encoding="utf-8"))
    except Exception: pass
    return []

def delete_history(index: int):
    try:
        if os.path.exists(HISTORY_FILE):
            data = json.load(open(HISTORY_FILE, "r", encoding="utf-8"))
            if 0 <= index < len(data):
                data.pop(index)
                json.dump(data, open(HISTORY_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    except Exception: pass

# ── 评分解析 ──
def parse_migration_scores(text: str) -> List[Dict[str, Any]]:
    items = []
    blocks = re.split(r"\n(?=###\s*(?:知识\s*)?迁移\s*\d+)", text)
    for block in blocks:
        if not block.strip(): continue
        title_match = re.search(r"###\s*(?:知识\s*)?迁移\s*\d+\s*[：:]\s*(.+?)(?:\n|$)", block)
        score_match = re.search(r"结构相似度[：:]\s*(\d+)", block)
        if title_match:
            items.append({
                "name": title_match.group(1).strip(),
                "score": int(score_match.group(1)) if score_match else 0,
                "block": block
            })
    return items

def render_stars(score: int) -> str:
    return "★" * score + "☆" * (5 - score)

def score_color(score: int) -> str:
    return {5: "var(--score-5)", 4: "var(--score-4)", 3: "var(--score-3)",
            2: "var(--score-2)", 1: "var(--score-1)"}.get(score, "var(--gray-400)")

# ── 页面配置 ──
st.set_page_config(
    page_title="知识迁移桥梁",
    layout="wide",
    page_icon="🌉",
    menu_items={"Get Help": None, "Report a bug": None,
                "About": "知识迁移桥梁 v3.1 — 基于认知科学类比推理的跨领域学习工具"},
)

# ═══════════════════════════════════════════════
# CSS 设计系统
# ═══════════════════════════════════════════════
st.markdown("""
<style>
/* ── Design Tokens ── */
:root {
    --purple-900: #1a1040; --purple-800: #2d1f6b; --purple-700: #3D2D80;
    --purple-600: #4a3a9e; --purple-500: #5B5FC7; --purple-400: #7b7fdb;
    --purple-300: #8B87FF; --purple-200: #b8b5ff; --purple-100: #e8e6ff;
    --purple-50: #f5f4ff;
    --gray-900: #1a1a2e; --gray-700: #3d3d5c; --gray-500: #8888a0;
    --gray-300: #c8c8d8; --gray-200: #e8e8f0; --gray-100: #f5f5f8;
    --gray-50: #fafafc;
    --green-500: #2d8c4e; --green-400: #34a853; --green-100: #e6f4ea;
    --red-500: #c73e3e; --red-400: #dc4a4a; --red-100: #fce8e6;
    --orange-500: #e08a2b; --orange-100: #fef3e4;
    --gold: #f0a500; --gold-light: #fff8e1;
    --score-5: #3D2D80; --score-4: #5B5FC7; --score-3: #8B87FF;
    --score-2: #b0b0d0; --score-1: #d0d0d8;
    --radius-sm: 8px; --radius-md: 12px; --radius-lg: 16px; --radius-xl: 20px;
    --shadow-xs: 0 1px 3px rgba(0,0,0,0.04);
    --shadow-sm: 0 2px 8px rgba(0,0,0,0.06);
    --shadow-md: 0 4px 16px rgba(0,0,0,0.08);
    --shadow-lg: 0 8px 32px rgba(0,0,0,0.12);
    --transition: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ── Dark Mode ── */
[data-theme="dark"] {
    --gray-900: #e8e8f0; --gray-700: #c8c8d8; --gray-500: #9999aa;
    --gray-300: #555568; --gray-200: #3a3a4a; --gray-100: #2a2a38;
    --gray-50: #1e1e2e;
}

/* ── Base ── */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] {
    font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 15px; line-height: 1.75; color: var(--gray-900);
}
h1 { font-size: 2rem; font-weight: 800; color: var(--purple-700); letter-spacing: -0.02em; }
h2 { font-size: 1.45rem; font-weight: 700; color: var(--gray-900); margin-top: 1.8rem; }
h3 { font-size: 1.15rem; font-weight: 600; color: var(--gray-700); margin-top: 1.4rem; }
.main .block-container { max-width: 1060px; padding: 1.5rem 2.5rem 5rem 2.5rem; }

/* ── Inputs ── */
div[data-testid="stTextInput"] input {
    border: 2px solid var(--gray-200); border-radius: var(--radius-md);
    padding: 0.75rem 1rem; font-size: 1rem; background: var(--gray-50);
    transition: var(--transition);
}
div[data-testid="stTextInput"] input:focus {
    border-color: var(--purple-500);
    box-shadow: 0 0 0 4px rgba(91,95,199,0.12); outline: none;
}

/* ── Buttons: Primary ── */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, var(--purple-500), var(--purple-300));
    color: white; border: none; border-radius: var(--radius-md);
    padding: 0.65rem 1.8rem; font-size: 0.95rem; font-weight: 600;
    transition: var(--transition); cursor: pointer;
    position: relative; overflow: hidden;
}
div[data-testid="stButton"] > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 24px rgba(91,95,199,0.35);
}
div[data-testid="stButton"] > button:active {
    transform: translateY(0); box-shadow: var(--shadow-xs);
}

/* ── Buttons: Outline (模板 / 历史) ── */
button[kind="secondary"], .stButton > button[kind="secondary"] {
    background: transparent !important; color: var(--purple-500) !important;
    border: 1.5px solid var(--purple-300) !important;
}
button[kind="secondary"]:hover {
    background: var(--purple-50) !important; border-color: var(--purple-500) !important;
}

/* ── Expanders ── */
section[data-testid="stExpander"] {
    border: 1px solid var(--gray-200); border-radius: var(--radius-lg);
    margin-bottom: 0.8rem; overflow: hidden;
    box-shadow: var(--shadow-xs); transition: var(--transition);
}
section[data-testid="stExpander"]:hover {
    box-shadow: var(--shadow-sm); border-color: var(--gray-300);
}

/* ── Tabs ── */
div[data-testid="stTabs"] button {
    font-weight: 500; font-size: 0.95rem; padding: 0.5rem 1.2rem;
    border-radius: var(--radius-md) var(--radius-md) 0 0;
    transition: var(--transition);
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--purple-500) !important; font-weight: 700;
    border-bottom: 3px solid var(--purple-500);
}

/* ── Progress Bar ── */
div[data-testid="stProgress"] > div {
    background: linear-gradient(90deg, var(--purple-500), var(--purple-300), var(--purple-200));
    border-radius: 8px; height: 8px;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f8f9fc 0%, #f0f1f8 100%);
}
section[data-testid="stSidebar"] .stExpander {
    border: none; box-shadow: none; background: transparent;
}

/* ── Cards ── */
.kb-card {
    background: var(--gray-50); border: 1px solid var(--gray-200);
    border-radius: var(--radius-lg); padding: 1.2rem;
    transition: var(--transition); box-shadow: var(--shadow-xs);
}
.kb-card:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); }

/* ── Migration Card ── */
.migration-card {
    background: white; border-radius: var(--radius-lg);
    padding: 1.2rem 1.5rem; margin: 0.8rem 0;
    border-left: 5px solid var(--purple-500);
    box-shadow: var(--shadow-xs); transition: var(--transition);
}
.migration-card:hover { box-shadow: var(--shadow-md); }
.migration-card.score-5 { border-left-color: var(--score-5); }
.migration-card.score-4 { border-left-color: var(--score-4); }
.migration-card.score-3 { border-left-color: var(--score-3); }
.migration-card.score-2 { border-left-color: var(--score-2); }
.migration-card.score-1 { border-left-color: var(--score-1); }

/* ── Score Badge ── */
.score-badge {
    display: inline-block; padding: 3px 12px; border-radius: 20px;
    font-size: 0.85rem; font-weight: 700; color: white;
    background: var(--purple-500);
}

/* ── Stepper ── */
.stepper-container {
    display: flex; justify-content: center; gap: 0;
    padding: 0.8rem 0 1.2rem 0;
}
.stepper-step {
    display: flex; align-items: center; gap: 0; font-size: 0.85rem;
}
.stepper-dot {
    width: 36px; height: 36px; border-radius: 50%; display: flex;
    align-items: center; justify-content: center; font-weight: 700;
    font-size: 0.9rem;
}
.stepper-dot.active { background: var(--purple-500); color: white; }
.stepper-dot.done { background: var(--green-500); color: white; }
.stepper-dot.pending { background: var(--gray-200); color: var(--gray-500); }
.stepper-line {
    width: 80px; height: 3px; border-radius: 2px;
}
.stepper-line.done { background: var(--green-500); }
.stepper-line.pending { background: var(--gray-200); }
.stepper-label { font-size: 0.82rem; margin-top: 4px; font-weight: 500; }
.stepper-label.active { color: var(--purple-500); font-weight: 700; }
.stepper-label.pending { color: var(--gray-500); }

/* ── Summary Stats ── */
.stats-grid { display: flex; gap: 1rem; flex-wrap: wrap; margin: 0.5rem 0 1rem 0; }
.stat-item {
    flex: 1; min-width: 120px; text-align: center; padding: 1rem;
    background: var(--gray-50); border-radius: var(--radius-md);
    border: 1px solid var(--gray-200);
}
.stat-value { font-size: 1.6rem; font-weight: 800; color: var(--purple-500); }
.stat-label { font-size: 0.78rem; color: var(--gray-500); margin-top: 2px; }

/* ── Fixed Bottom Bar ── */
.bottom-bar {
    position: fixed; bottom: 0; left: 0; right: 0; z-index: 999;
    background: white; border-top: 1px solid var(--gray-200);
    padding: 0.7rem 2rem; display: flex; align-items: center;
    justify-content: space-between; gap: 1rem;
    box-shadow: 0 -2px 12px rgba(0,0,0,0.06);
}

/* ── Status Dot ── */
.status-dot {
    display: inline-block; width: 10px; height: 10px; border-radius: 50%;
    margin-right: 6px; animation: pulse 2s infinite;
}
.status-dot.green { background: var(--green-400); }
.status-dot.red { background: var(--red-400); }
.status-dot.orange { background: var(--orange-500); }

@keyframes pulse {
    0%, 100% { opacity: 1; } 50% { opacity: 0.5; }
}
@keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}
.animate-in { animation: slideUp 0.4s ease-out; }

/* ── Blockquote ── */
blockquote {
    border-left: 4px solid var(--purple-500); background: var(--purple-50);
    padding: 0.9rem 1.3rem; margin: 1rem 0; border-radius: 0 var(--radius-md) var(--radius-md) 0;
    color: var(--gray-700);
}

/* ── Dividers & Misc ── */
hr { border: none; border-top: 1.5px solid var(--gray-200); margin: 2rem 0; }
.star-rating { font-size: 1.1rem; color: var(--gold); letter-spacing: 3px; }
.follow-up-box {
    background: var(--gray-50); border-radius: var(--radius-md); padding: 1rem;
    border-left: 3px solid var(--purple-500); margin: 0.5rem 0 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# ── 标题 ──
st.title("🌉 知识迁移桥梁")
st.caption("从你熟悉的领域出发，用类比理解任何新领域 —— 基于认知科学中的结构映射理论")

# ═══════════════════════════════════════════════
# Session State
# ═══════════════════════════════════════════════
for key, default in [
    ("results", {}), ("meta", {}), ("running", False),
    ("source_domain", ""), ("target_domain", ""), ("template_used", ""),
    ("flagged_items", []), ("follow_up_answers", {}),
    ("restore_results", None), ("restore_meta", None), ("restore_flagged", None),
    ("current_step", 0),
]:
    if key not in st.session_state: st.session_state[key] = default

if st.session_state.restore_results is not None:
    st.session_state.results = st.session_state.restore_results
    st.session_state.meta = st.session_state.restore_meta or {}
    st.session_state.flagged_items = st.session_state.restore_flagged or []
    st.session_state.restore_results = st.session_state.restore_meta = st.session_state.restore_flagged = None
    st.session_state.current_step = 2
    st.info("📂 已加载历史记录，请在下方查看结果。")

# ═══════════════════════════════════════════════
# 侧边栏
# ═══════════════════════════════════════════════
with st.sidebar:
    # ── API 配置 ──
    with st.expander("⚙️ API 配置", expanded=(not LLM_API_KEY)):
        api_key = st.text_input("API Key", type="password", value=LLM_API_KEY, label_visibility="collapsed",
                                placeholder="输入你的 API Key")
        c1, c2 = st.columns(2)
        with c1: base_url = st.text_input("Base URL", value=LLM_BASE_URL, label_visibility="collapsed")
        with c2: model = st.text_input("模型", value=LLM_MODEL, label_visibility="collapsed")

    # ── 状态指示器 ──
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:8px;margin:8px 0 12px 0;
         padding:8px 12px;background:var(--gray-100);border-radius:8px;">
        <span class="status-dot {'green' if api_key else 'orange'}"></span>
        <span style="font-size:0.82rem;font-weight:500;">
            {'🟢 API 已配置' if api_key else '🟠 请填写 API Key'}
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── 领域模板 (折叠) ──
    with st.expander("📋 领域模板（8组预设）", expanded=False):
        cols_t = st.columns(2)
        for i, (label, src, tgt, tip) in enumerate(TEMPLATES):
            with cols_t[i % 2]:
                if st.button(f"📌 {label}", key=f"tpl_{i}", use_container_width=True, help=tip):
                    st.session_state.source_domain = src
                    st.session_state.target_domain = tgt
                    st.session_state.template_used = label
                    st.rerun()

    # ── 历史记录 (折叠) ──
    with st.expander("📚 历史记录", expanded=False):
        history = load_history()
        if history:
            st.caption(f"共 {len(history)} 条记录")
            for idx, h in enumerate(history[:5]):
                col_h, col_d = st.columns([4, 1])
                with col_h:
                    label = h.get("template", f"{h.get('src','?')} → {h.get('tgt','?')}")
                    ts = h.get("timestamp", "")[:16]
                    if st.button(f"📄 {label}", key=f"hist_{idx}", help=f"时间: {ts}", use_container_width=True):
                        st.session_state.source_domain = h.get("src", "")
                        st.session_state.target_domain = h.get("tgt", "")
                        st.session_state.restore_results = h.get("results", {})
                        st.session_state.restore_meta = h.get("meta", {})
                        st.session_state.restore_flagged = h.get("flagged", [])
                        st.rerun()
                with col_d:
                    if st.button("✕", key=f"del_{idx}"):
                        delete_history(idx); st.rerun()
            if st.button("🗑️ 清空全部", use_container_width=True):
                if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)
                st.rerun()
        else:
            st.caption("暂无历史记录")

    st.divider()

    # ── 缓存状态 ──
    cs = cache_stats()
    if cs["hits"] + cs["misses"] > 0:
        st.caption(f"💾 缓存: {cs['hits']} 命中 / {cs['misses']} 未命中")
    if st.button("🔄 刷新页面", use_container_width=True):
        clear_cache(); st.rerun()

# ═══════════════════════════════════════════════
# 步骤条
# ═══════════════════════════════════════════════
step = st.session_state.current_step
if st.session_state.results: step = 2
elif st.session_state.running: step = 1
else: step = 0

steps = [("①", "输入领域", "声明已知与未知"),
         ("②", "知识迁移", "四阶段流水线执行"),
         ("③", "查看结果", "类比分析 + 追问 + 导出")]

cols_step = st.columns([1, 0.15, 0.15, 1, 0.15, 0.15, 1])
step_data = [(0, 0), (0, 3), (0, 6)]  # column indices for each step
for i, ((icon, title, desc), (_, col_idx)) in enumerate(zip(steps, step_data)):
    with cols_step[col_idx]:
        dot_class = "active" if i == step else ("done" if i < step else "pending")
        label_class = "active" if i == step else ("pending" if i > step else "")
        dot_symbol = "✓" if i < step else icon
        st.markdown(f"""
        <div style="text-align:center;">
            <div class="stepper-dot {dot_class}" style="margin:0 auto;">{dot_symbol}</div>
            <div class="stepper-label {label_class}" style="text-align:center;">{title}</div>
            <div style="font-size:0.7rem;color:var(--gray-500);text-align:center;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
    # Connector line
    if i < 2:
        with cols_step[col_idx + 1]:
            line_class = "done" if i < step else "pending"
            st.markdown(f"""
            <div style="display:flex;align-items:center;justify-content:center;height:36px;">
                <div class="stepper-line {line_class}" style="width:100%;"></div>
            </div>
            """, unsafe_allow_html=True)

st.divider()

# ═══════════════════════════════════════════════
# 输入区域
# ═══════════════════════════════════════════════
st.subheader("第一步：声明你的已知与未知")
col1, col2, col3 = st.columns([3, 0.3, 3])
with col1:
    source_domain = st.text_input("你擅长的领域", placeholder="例如：厨艺、足球、音乐、法律、摄影……",
                                  value=st.session_state.source_domain, label_visibility="visible")
with col3:
    target_domain = st.text_input("你想学习的领域", placeholder="例如：机器学习、量子计算、经济学、哲学……",
                                  value=st.session_state.target_domain, label_visibility="visible")
if st.session_state.template_used:
    st.caption(f"📌 已选用模板：{st.session_state.template_used}")

# ── 运行按钮 ──
run_col1, run_col2 = st.columns([1.5, 5])
with run_col1:
    start = st.button("🚀 开始知识迁移", type="primary", use_container_width=True)

if start:
    if not source_domain or not target_domain: st.warning("请填写两个领域后再开始。")
    elif not api_key: st.warning("请在侧边栏填写 API Key。")
    else:
        st.session_state.source_domain = source_domain
        st.session_state.target_domain = target_domain
        st.session_state.results = {}
        st.session_state.meta = {}
        st.session_state.flagged_items = []
        st.session_state.follow_up_answers = {}
        st.session_state.current_step = 1
        st.session_state.running = True
        st.rerun()

# ═══════════════════════════════════════════════
# 流水线执行
# ═══════════════════════════════════════════════
if st.session_state.running and st.session_state.source_domain:
    bridge = KnowledgeBridge()
    bridge.llm = type(bridge.llm)(api_key=api_key, base_url=base_url, model=model)

    st.subheader("第二步：知识迁移进行中")
    progress_bar = st.progress(0, text="准备启动...")
    status_area = st.empty()
    stage_status = st.empty()

    stage_icons = ["🔍", "🔎", "🧠", "📝"]
    stage_names = [
        f"提取「{st.session_state.source_domain}」概念图谱",
        f"提取「{st.session_state.target_domain}」概念图谱",
        "建立跨领域知识迁移",
        "生成理解检验题",
    ]

    all_results = {}
    all_meta = {}
    error_occurred = False
    warnings_list = []

    try:
        for stage, content, meta in bridge.run(st.session_state.source_domain, st.session_state.target_domain):
            all_results[stage] = content
            all_meta[stage] = meta
            progress_bar.progress(stage * 25, text=f"阶段 {stage}/4")

            # 更新阶段卡片状态
            done_icons = " ".join([f"<span style='font-size:1.3rem;'>{stage_icons[i]}</span>"
                                   for i in range(stage)])
            pending_icons = " ".join([f"<span style='font-size:1.3rem;opacity:0.3;'>{stage_icons[i]}</span>"
                                      for i in range(stage, 4)])
            retry_count = meta.get("retry_count", 0)
            cache_text = " ⚡缓存命中" if meta.get("cached") else ""
            retry_text = f" 🔄重试{retry_count}次" if retry_count > 0 else ""
            stage_status.markdown(f"""
            <div style="display:flex;justify-content:center;gap:1.5rem;padding:1rem 0;
                 font-size:0.9rem;flex-wrap:wrap;">
                {done_icons} {pending_icons}
            </div>
            <div style="text-align:center;color:var(--gray-500);font-size:0.85rem;">
                已完成 {stage}/4 阶段{cache_text}{retry_text}
            </div>
            """, unsafe_allow_html=True)

            if meta.get("issues"):
                for iss in meta["issues"]: warnings_list.append(f"阶段{stage}: {iss}")

            if meta.get("parallel_elapsed_s") and stage == 2:
                status_area.info(f"⚡ 阶段 1+2 并行耗时 **{meta['parallel_elapsed_s']}s**")

    except Exception as e:
        st.error(f"流水线严重错误: {e}")
        error_occurred = True
    finally:
        st.session_state.results = all_results
        st.session_state.meta = all_meta
        st.session_state.running = False
        st.session_state.current_step = 2

    progress_bar.progress(100, text="知识迁移完成！")
    stage_status.empty()

    # ── 运行摘要面板 ──
    total_cached = sum(1 for m in all_meta.values() if m.get("cached"))
    total_retries = sum(m.get("retry_count", 0) for m in all_meta.values())
    total_issues = len(warnings_list)
    first_meta = all_meta.get(1, {})
    parallel_time = first_meta.get("parallel_elapsed_s", "?")

    if not error_occurred:
        s_cols = st.columns(4)
        stats_items = [
            ("⚡", f"{parallel_time}s", "并行耗时"),
            ("💾", str(total_cached), "缓存命中"),
            ("🔄", str(total_retries), "自动重试"),
            ("✅", str(4 - total_issues), "阶段通过"),
        ]
        for col, (icon, val, lbl) in zip(s_cols, stats_items):
            with col:
                st.markdown(f"""
                <div class="stat-item animate-in">
                    <div style="font-size:1.4rem;">{icon}</div>
                    <div class="stat-value">{val}</div>
                    <div class="stat-label">{lbl}</div>
                </div>
                """, unsafe_allow_html=True)

    if warnings_list:
        with st.expander(f"⚠️ {len(warnings_list)} 个格式告警", expanded=False):
            for w in warnings_list: st.warning(w)
    if total_retries > 0:
        st.info(f"🔄 本次运行触发 {total_retries} 次自动重试，运行基本正常。")

# ═══════════════════════════════════════════════
# 结果展示
# ═══════════════════════════════════════════════
results = st.session_state.results
if results:
    st.divider()
    st.subheader("第三步：查看迁移结果")

    src = st.session_state.source_domain
    tgt = st.session_state.target_domain
    stage3_content = results.get(3, "")

    # ── Tab 切换视图 ──
    tab1, tab2, tab3, tab4 = st.tabs(["📊 评分总览", "🔍 概念图谱", "🧠 类比迁移", "📝 检验题"])

    with tab1:
        # 评分可视化
        if stage3_content:
            items = parse_migration_scores(stage3_content)
            if items:
                st.caption(f"从 {src} 到 {tgt} 的 {len(items)} 个知识迁移对")
                cols_viz = st.columns(min(len(items), 4))
                for i, item in enumerate(items):
                    with cols_viz[i % 4]:
                        s = item["score"]
                        st.markdown(f"""
                        <div class="kb-card animate-in" style="text-align:center;padding:1rem;">
                            <div style="font-size:0.85rem;color:var(--gray-700);margin-bottom:8px;
                                 min-height:40px;line-height:1.3;">{item['name'][:30]}</div>
                            <div class="star-rating">{render_stars(s)}</div>
                            <div style="margin-top:5px;">
                                <span class="score-badge" style="background:{score_color(s)};">
                                    {s}/5
                                </span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                # 评分分布条
                score_counts = {i: sum(1 for it in items if it["score"] == i) for i in range(1, 6)}
                max_count = max(score_counts.values()) or 1
                st.caption("评分分布")
                dist_cols = st.columns(5)
                for i, col in enumerate(dist_cols, 1):
                    count = score_counts[i]
                    pct = count / len(items) * 100
                    with col:
                        st.markdown(f"""
                        <div style="text-align:center;font-size:0.8rem;">
                            <div style="font-weight:700;">{render_stars(i)[:i]}</div>
                            <div style="background:var(--gray-200);border-radius:6px;height:8px;margin:4px 0;
                                 overflow:hidden;">
                                <div style="background:{score_color(i)};height:100%;width:{pct}%;
                                     border-radius:6px;transition:width 0.6s ease;"></div>
                            </div>
                            <div style="color:var(--gray-500);">{count}个</div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("未能从 Stage 3 输出中解析出类比迁移对。")

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            with st.expander(f"源领域：{src}", expanded=True):
                st.markdown(results.get(1, "(无内容)"))
        with c2:
            with st.expander(f"目标领域：{tgt}", expanded=True):
                st.markdown(results.get(2, "(无内容)"))

    with tab3:
        if stage3_content:
            st.markdown(stage3_content)

            # ── 标记存疑 ──
            st.divider()
            fc1, fc2 = st.columns([1, 3])
            with fc1:
                flag_reason = st.text_input("标记存疑的类比", placeholder="如：摆盘 → 模型评估",
                                            key="flag_input_3", label_visibility="collapsed")
            with fc2:
                if st.button("⚠️ 标记存疑", key="flag_btn_3"):
                    if flag_reason.strip():
                        if flag_reason.strip() not in st.session_state.flagged_items:
                            st.session_state.flagged_items.append(flag_reason.strip())
                        st.success(f"已标记「{flag_reason.strip()}」")
                    else: st.warning("请填写类比名称")
            if st.session_state.flagged_items:
                st.info("📌 已存疑：" + " · ".join(st.session_state.flagged_items))

            # ── 交互式追问 ──
            st.divider()
            st.caption("💬 对某个类比不理解？换个角度为你解释。")
            fu_col1, fu_col2 = st.columns([3, 1])
            with fu_col1:
                follow_up_q = st.text_input("你的问题", placeholder="如：换个角度解释「火候 → 训练过程」",
                                            key="follow_up_input", label_visibility="collapsed")
            with fu_col2:
                if st.button("🙋 追问", type="primary", key="follow_up_btn", use_container_width=True):
                    if follow_up_q.strip():
                        with st.spinner("正在思考..."):
                            b2 = KnowledgeBridge()
                            b2.llm = type(b2.llm)(api_key=api_key, base_url=base_url, model=model)
                            answer = b2.follow_up(stage3_content, follow_up_q.strip())
                            key = f"q{len(st.session_state.follow_up_answers)}"
                            st.session_state.follow_up_answers[key] = {
                                "question": follow_up_q.strip(),
                                "answer": answer,
                                "time": datetime.now().strftime("%H:%M:%S"),
                            }
                        st.rerun()

            if st.session_state.follow_up_answers:
                for key, item in reversed(list(st.session_state.follow_up_answers.items())):
                    with st.expander(f"❓ {item['question'][:60]}… ({item['time']})", expanded=False):
                        st.markdown(f"""<div class="follow-up-box">{item['answer']}</div>""",
                                    unsafe_allow_html=True)

    with tab4:
        st.markdown(results.get(4, "(无内容)"))

    # ── 悬浮底部导出栏 ──
    st.divider()

    flagged_note = ""
    if st.session_state.flagged_items:
        flagged_note = "\n\n> ⚠️ 存疑标记：\n> " + "\n> ".join(st.session_state.flagged_items)

    export_md = f"""# 知识迁移报告
> **生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> **源领域**：{src} | **目标领域**：{tgt}{flagged_note}

---

## 阶段一：源领域概念图谱 —— {src}
{results.get(1, '(无内容)')}

---

## 阶段二：目标领域概念图谱 —— {tgt}
{results.get(2, '(无内容)')}

---

## 阶段三：跨领域知识迁移
{results.get(3, '(无内容)')}

---

## 阶段四：类比理解检验题
{results.get(4, '(无内容)')}

---

> 由「知识迁移桥梁 v3.1」自动生成 | 基于认知科学类比推理理论
"""

    exp_col1, exp_col2, exp_col3 = st.columns([1.5, 1.5, 4])
    with exp_col1:
        st.download_button("📥 导出 Markdown", data=export_md,
                           file_name=f"知识迁移_{src}_to_{tgt}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                           mime="text/markdown", use_container_width=True)
    with exp_col2:
        if st.button("💾 保存记录", use_container_width=True):
            save_history({
                "src": src, "tgt": tgt, "template": st.session_state.template_used,
                "timestamp": datetime.now().isoformat(),
                "results": {str(k): v for k, v in results.items()},
                "meta": {str(k): v for k, v in st.session_state.meta.items()},
                "flagged": st.session_state.flagged_items,
            })
            st.success("✅ 已保存！")
    with exp_col3:
        share_md = f"我用「知识迁移桥梁」把「{src}」的知识迁移到了「{tgt}」！🌉 试试看：https://knowledge-bridge.streamlit.app"
        st.code(share_md, language=None)
        st.caption("👆 复制上方文案分享给朋友")
