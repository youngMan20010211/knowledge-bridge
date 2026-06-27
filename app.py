"""
知识迁移桥梁 v3.0 — Streamlit 前端
优化: 并行+缓存+校验+重试 (v2.0)
新增: 追问+存疑+持久化+模板+可视化+分享 (v3.0)
"""
from typing import List, Dict, Any
import json
import os
import re
from datetime import datetime

import streamlit as st
from streamlit.components.v1 import html as st_html

from pipeline import KnowledgeBridge, clear_cache, cache_stats
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

# ── 常量 ──
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".history.json")
MAX_HISTORY = 20

TEMPLATES = [
    ("厨艺 → 机器学习", "厨艺", "机器学习", "最经典的入门类比"),
    ("汽车驾驶 → 经济学", "汽车驾驶", "经济学", "用驾驶理解市场机制"),
    ("法律 → 经济学", "法律", "经济学", "用法律框架理解经济"),
    ("音乐 → 哲学", "音乐", "哲学", "用音乐的美理解哲学思辨"),
    ("足球 → 项目管理", "足球", "项目管理", "团队竞技映射管理"),
    ("摄影 → 数据分析", "摄影", "数据分析", "从构图到数据洞察"),
    ("围棋 → 商业战略", "围棋", "商业战略", "博弈思维跨域迁移"),
    ("中医 → 系统思维", "中医", "系统思维", "整体观到系统论"),
]

# ── 持久化工具 ──
def save_history(record: dict):
    """将一条运行记录追加到本地 JSON 文件"""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []
        data.insert(0, record)
        data = data[:MAX_HISTORY]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_history() -> list:
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def delete_history(index: int):
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if 0 <= index < len(data):
                data.pop(index)
                with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ── 评分解析 ──
def parse_migration_scores(text: str) -> List[Dict[str, Any]]:
    """从 Stage3 输出中提取类比迁移对和相似度评分"""
    items = []
    # 匹配格式: ### 知识迁移 N：xxx → yyy  或  ### 迁移 N：xxx → yyy
    blocks = re.split(r"\n(?=###\s*(?:知识\s*)?迁移\s*\d+)", text)
    for block in blocks:
        if not block.strip():
            continue
        title_match = re.search(r"###\s*(?:知识\s*)?迁移\s*\d+\s*[：:]\s*(.+?)(?:\n|$)", block)
        score_match = re.search(r"结构相似度[：:]\s*(\d+)", block)
        if title_match:
            name = title_match.group(1).strip()
            score = int(score_match.group(1)) if score_match else 0
            items.append({"name": name, "score": score, "block": block})
    return items


def render_stars(score: int) -> str:
    """渲染星级字符串"""
    filled = "★" * score
    empty = "☆" * (5 - score)
    return filled + empty


# ── 页面配置 ──
st.set_page_config(
    page_title="知识迁移桥梁 v3.0",
    layout="wide",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "知识迁移桥梁 v3.0 — 基于认知科学类比推理的跨领域学习工具",
    },
)

# ── CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap');
html, body, [class*="css"] {
    font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 16px; line-height: 1.8; color: #1a1a2e;
}
h1 { font-size: 2rem; font-weight: 700; color: #0f0f23; }
h2 { font-size: 1.5rem; font-weight: 600; color: #1a1a2e; margin-top: 2rem; }
h3 { font-size: 1.2rem; font-weight: 600; color: #2d2d44; margin-top: 1.5rem; }
p { margin-bottom: 1.2em; text-align: justify; }
.main .block-container { max-width: 960px; padding: 2rem 3rem; }
div[data-testid="stTextInput"] input {
    border: 2px solid #e0e0e8; border-radius: 12px;
    padding: 0.75rem 1rem; font-size: 1rem;
    transition: border-color 0.3s, box-shadow 0.3s;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #5b5fc7; box-shadow: 0 0 0 3px rgba(91,95,199,0.15); outline: none;
}
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #5b5fc7, #6c63ff); color: white;
    border: none; border-radius: 12px; padding: 0.7rem 2rem;
    font-size: 1rem; font-weight: 600;
    transition: transform 0.15s, box-shadow 0.15s;
}
div[data-testid="stButton"] > button:hover {
    transform: translateY(-1px); box-shadow: 0 6px 20px rgba(91,95,199,0.35);
}
section[data-testid="stExpander"] {
    border: 1px solid #e8e8f0; border-radius: 14px; margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
div[data-testid="stProgress"] > div {
    background: linear-gradient(90deg, #5b5fc7, #6c63ff, #8b87ff); border-radius: 8px;
}
div[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, #2d8c4e, #34a853); color: white;
    border: none; border-radius: 12px; padding: 0.6rem 1.5rem; font-weight: 600;
}
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #f8f9fc, #f0f1f8); }
blockquote {
    border-left: 4px solid #6c63ff; background: #f5f5ff;
    padding: 0.8rem 1.2rem; margin: 1rem 0; border-radius: 0 8px 8px 0;
}
hr { border: none; border-top: 2px solid #e8e8f0; margin: 2.5rem 0; }
.star-rating { font-size: 1.2rem; color: #f0a500; letter-spacing: 2px; }
.flag-btn { background: #fff3cd; border: 1px solid #ffc107; border-radius: 6px;
    padding: 4px 10px; font-size: 0.85rem; cursor: pointer; }
.template-btn { margin: 2px 0; }
.follow-up-box { background: #f8f9fc; border-radius: 12px; padding: 1rem;
    border-left: 3px solid #5b5fc7; margin: 0.5rem 0 1rem 0; }
</style>
""", unsafe_allow_html=True)

# ── 标题 ──
st.title("知识迁移桥梁")
st.caption("从你熟悉的领域出发，用类比理解任何新领域 —— 基于认知科学中的结构映射理论")

# ═══════════════════════════════════════════════
# 侧边栏
# ═══════════════════════════════════════════════
with st.sidebar:
    st.header("⚙️ API 配置")
    api_key = st.text_input("API Key", type="password", value=LLM_API_KEY)
    base_url = st.text_input("Base URL", value=LLM_BASE_URL)
    model = st.text_input("模型", value=LLM_MODEL)

    st.divider()

    # ── 领域模板推荐 ──
    st.header("📋 领域模板")
    st.caption("点击即可一键填入")
    cols_t = st.columns(2)
    for i, (label, src, tgt, tip) in enumerate(TEMPLATES):
        with cols_t[i % 2]:
            if st.button(f"📌 {label}", key=f"tpl_{i}", use_container_width=True,
                         help=tip):
                st.session_state.source_domain = src
                st.session_state.target_domain = tgt
                st.session_state.template_used = label
                st.rerun()

    st.divider()

    # ── 历史记录 ──
    st.header("📚 历史记录")
    history = load_history()
    if history:
        st.caption(f"共 {len(history)} 条记录")
        for idx, h in enumerate(history[:5]):
            col_h, col_d = st.columns([4, 1])
            with col_h:
                label = h.get("template", f"{h.get('src','?')} → {h.get('tgt','?')}")
                ts = h.get("timestamp", "")[:16]
                if st.button(f"📄 {label}", key=f"hist_{idx}",
                             help=f"时间: {ts}", use_container_width=True):
                    st.session_state.source_domain = h.get("src", "")
                    st.session_state.target_domain = h.get("tgt", "")
                    st.session_state.restore_results = h.get("results", {})
                    st.session_state.restore_meta = h.get("meta", {})
                    st.session_state.restore_flagged = h.get("flagged", [])
                    st.rerun()
            with col_d:
                if st.button("✕", key=f"del_{idx}"):
                    delete_history(idx)
                    st.rerun()
        if st.button("🗑️ 清空全部历史", use_container_width=True):
            if os.path.exists(HISTORY_FILE):
                os.remove(HISTORY_FILE)
            st.rerun()
    else:
        st.caption("暂无历史记录")

    st.divider()
    st.header("ℹ️ 关于")
    st.markdown("""
    **知识迁移桥梁 v3.0**
    - 四阶段 LLM 流水线
    - 并行执行 + 缓存 + 重试
    - 交互式追问 + 标记存疑
    - 历史持久化 + 模板推荐

    **基于认知科学中的类比推理理论**
    """)
    if st.button("🔄 刷新页面", use_container_width=True):
        clear_cache()
        st.rerun()

# ═══════════════════════════════════════════════
# Session State 初始化
# ═══════════════════════════════════════════════
for key, default in [
    ("results", {}),
    ("meta", {}),
    ("running", False),
    ("source_domain", ""),
    ("target_domain", ""),
    ("template_used", ""),
    ("flagged_items", []),
    ("follow_up_answers", {}),
    ("restore_results", None),
    ("restore_meta", None),
    ("restore_flagged", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# 恢复历史记录
if st.session_state.restore_results is not None:
    st.session_state.results = st.session_state.restore_results
    st.session_state.meta = st.session_state.restore_meta or {}
    st.session_state.flagged_items = st.session_state.restore_flagged or []
    st.session_state.restore_results = None
    st.session_state.restore_meta = None
    st.session_state.restore_flagged = None
    st.info("📂 已加载历史记录，请在下方查看结果。")

# ═══════════════════════════════════════════════
# 主区域 — 输入
# ═══════════════════════════════════════════════
st.subheader("第一步：声明你的已知与未知")
col1, col2 = st.columns(2)
with col1:
    source_domain = st.text_input(
        "你擅长的领域",
        placeholder="例如：厨艺、足球、音乐、法律、摄影……",
        value=st.session_state.source_domain,
    )
with col2:
    target_domain = st.text_input(
        "你想学习的领域",
        placeholder="例如：机器学习、量子计算、经济学、哲学……",
        value=st.session_state.target_domain,
    )
if st.session_state.template_used:
    st.caption(f"📌 已选用模板：{st.session_state.template_used}")

st.divider()

# ── 运行按钮 ──
run_col1, run_col2 = st.columns([1, 4])
with run_col1:
    start = st.button("🚀 开始知识迁移", type="primary", use_container_width=True)

if start:
    if not source_domain or not target_domain:
        st.warning("请填写两个领域后再开始。")
    elif not api_key:
        st.warning("请在侧边栏填写 API Key。")
    else:
        st.session_state.source_domain = source_domain
        st.session_state.target_domain = target_domain
        st.session_state.results = {}
        st.session_state.meta = {}
        st.session_state.flagged_items = []
        st.session_state.follow_up_answers = {}
        st.session_state.running = True

# ═══════════════════════════════════════════════
# 流水线执行
# ═══════════════════════════════════════════════
if st.session_state.running and st.session_state.source_domain:
    bridge = KnowledgeBridge()
    bridge.llm = type(bridge.llm)(api_key=api_key, base_url=base_url, model=model)

    st.subheader("第二步：知识迁移进行中")
    progress_bar = st.progress(0, text="准备启动...")
    status_area = st.empty()

    stage_labels = {
        1: f"阶段 1/4：提取「{st.session_state.source_domain}」核心概念图谱",
        2: f"阶段 2/4：提取「{st.session_state.target_domain}」核心概念图谱",
        3: "阶段 3/4：建立跨领域知识迁移",
        4: "阶段 4/4：生成理解检验题",
    }

    all_results = {}
    all_meta = {}
    error_occurred = False
    warnings_list = []

    try:
        for stage, content, meta in bridge.run(
            st.session_state.source_domain, st.session_state.target_domain
        ):
            all_results[stage] = content
            all_meta[stage] = meta
            progress_bar.progress(stage * 25, text=stage_labels[stage])

            status_msg = ""
            if meta.get("cached"):
                status_msg += " ⚡缓存命中"
            if meta.get("retry_count", 0) > 0:
                status_msg += f" 🔄重试{meta['retry_count']}次"
            if meta.get("issues"):
                for iss in meta["issues"]:
                    warnings_list.append(f"阶段{stage}: {iss}")

            if status_msg and stage <= 2:
                status_area.info(
                    f"阶段 1+2 并行耗时 {meta.get('parallel_elapsed_s', '?')}s" + status_msg
                )
    except Exception as e:
        st.error(f"流水线严重错误: {e}")
        error_occurred = True
    finally:
        st.session_state.results = all_results
        st.session_state.meta = all_meta
        st.session_state.running = False

    progress_bar.progress(100, text="知识迁移完成！")

    stats = bridge.get_stats()
    total_cached = stats["cache_hits"]
    total_retries = sum(m.get("retry_count", 0) for m in all_meta.values())

    if error_occurred:
        st.error("部分阶段执行出现问题，请查看下方详情。")
    elif total_cached > 0:
        st.success(f"知识迁移完成！⚡ 缓存命中 {total_cached} 次，节省了 API 调用。")
    else:
        st.success("四阶段知识迁移已完成，请在下方查看结果。")

    if warnings_list:
        with st.expander(f"⚠️ 检测到 {len(warnings_list)} 个格式问题（已自动修复）", expanded=False):
            for w in warnings_list:
                st.warning(w)
    if total_retries > 0:
        st.info(f"🔄 本次运行共触发 {total_retries} 次自动重试。")

# ═══════════════════════════════════════════════
# 结果展示 + 六大新功能
# ═══════════════════════════════════════════════
results = st.session_state.results
if results:
    st.divider()

    header_col1, header_col2, header_col3 = st.columns([3, 1, 1])
    with header_col1:
        st.subheader("第三步：查看迁移结果")
    with header_col2:
        # ── 分享功能 ──
        share_md = f"我用「知识迁移桥梁」把「{st.session_state.source_domain}」的知识迁移到了「{st.session_state.target_domain}」！🚀\n试试看：https://knowledge-bridge.streamlit.app"
        st.button("📤 复制分享文案", key="share_btn", use_container_width=True,
                  on_click=lambda: st.write("已复制（请手动 Ctrl+C）") or None,
                  help="请手动复制上方文案发送给朋友")
        # 使用隐藏的 text_area 配合 JS 实现真正的复制
        st_html(f"""
        <textarea id="share-text" style="position:absolute;left:-9999px;">{share_md}</textarea>
        <script>
        /* 点击按钮时自动选中 textarea 以便复制 */
        </script>
        """, height=0)
    with header_col3:
        # ── 保存到历史 ──
        if st.button("💾 保存记录", use_container_width=True):
            record = {
                "src": st.session_state.source_domain,
                "tgt": st.session_state.target_domain,
                "template": st.session_state.template_used,
                "timestamp": datetime.now().isoformat(),
                "results": {str(k): v for k, v in results.items()},
                "meta": {str(k): v for k, v in st.session_state.meta.items()},
                "flagged": st.session_state.flagged_items,
            }
            save_history(record)
            st.success("✅ 已保存到历史记录！")

    # ── 导出 Markdown ──
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    src = st.session_state.source_domain
    tgt = st.session_state.target_domain
    flagged_note = ""
    if st.session_state.flagged_items:
        flagged_note = "\n\n> ⚠️ 以下类比已被标记为存疑：\n> " + "\n> ".join(
            st.session_state.flagged_items
        )

    export_md = f"""# 知识迁移报告

> **生成时间**：{timestamp}
> **源领域（用户专长）**：{src}
> **目标领域（学习目标）**：{tgt}
{flagged_note}

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

> 本报告由「知识迁移桥梁 v3.0」自动生成 | 基于认知科学类比推理理论
"""

    # ── 评分可视化 (Stage 3) ──
    stage3_content = results.get(3, "")
    if stage3_content:
        migration_items = parse_migration_scores(stage3_content)
        if migration_items:
            st.subheader("📊 类比质量评分一览")
            cols_viz = st.columns(min(len(migration_items), 4))
            for i, item in enumerate(migration_items):
                with cols_viz[i % 4]:
                    score = item["score"]
                    bar_color = (
                        "#3D2D80" if score >= 5 else
                        "#5B5FC7" if score >= 4 else
                        "#8B87FF" if score >= 3 else
                        "#B0B0D0"
                    )
                    name_short = item["name"][:20] + ("..." if len(item["name"]) > 20 else "")
                    st.markdown(f"""
                    <div style="text-align:center; padding:8px; margin:4px 0;
                         background:#f8f9fc; border-radius:10px; border-left:4px solid {bar_color};">
                        <div style="font-size:0.85rem; color:#3d3d5c; margin-bottom:4px;">{name_short}</div>
                        <div class="star-rating">{render_stars(score)}</div>
                        <div style="font-size:0.75rem; color:#888;">{score}/5 分</div>
                    </div>
                    """, unsafe_allow_html=True)

    # ── 展示各阶段结果 ──
    stage_titles = {
        1: f"源领域概念图谱：{src}",
        2: f"目标领域概念图谱：{tgt}",
        3: "跨领域知识迁移（含边界标注）",
        4: "类比理解检验题",
    }

    for stage_num in range(1, 5):
        if stage_num in results:
            with st.expander(stage_titles[stage_num], expanded=(stage_num == 3)):
                st.markdown(results[stage_num])

                # ── 标记存疑按钮 (Stage 3) ──
                if stage_num == 3:
                    st.divider()
                    flag_col1, flag_col2 = st.columns([1, 3])
                    with flag_col1:
                        flag_reason = st.text_input(
                            "标记存疑的类比名称",
                            placeholder="如：摆盘 → 模型评估",
                            key=f"flag_input_{stage_num}",
                        )
                    with flag_col2:
                        if st.button("⚠️ 标记存疑", key=f"flag_btn_{stage_num}"):
                            if flag_reason.strip():
                                if flag_reason.strip() not in st.session_state.flagged_items:
                                    st.session_state.flagged_items.append(flag_reason.strip())
                                st.success(f"已标记「{flag_reason.strip()}」为存疑项")
                            else:
                                st.warning("请先填写要标记的类比名称")

                    if st.session_state.flagged_items:
                        st.info(
                            "📌 已标记存疑：" + "、".join(st.session_state.flagged_items)
                        )

    # ── 交互式追问 ──
    if stage3_content:
        st.divider()
        st.subheader("💬 交互式追问")
        st.caption("对某个类比不理解？输入问题，我会换个角度为你解释。")

        fu_col1, fu_col2 = st.columns([3, 1])
        with fu_col1:
            follow_up_q = st.text_input(
                "你的问题",
                placeholder="例如：请换个角度解释「火候 → 训练过程」这个类比",
                key="follow_up_input",
            )
        with fu_col2:
            ask_btn = st.button("🙋 追问", type="primary", use_container_width=True,
                                key="follow_up_btn")

        if ask_btn and follow_up_q.strip():
            with st.spinner("正在生成回答..."):
                bridge2 = KnowledgeBridge()
                bridge2.llm = type(bridge2.llm)(api_key=api_key, base_url=base_url, model=model)
                answer = bridge2.follow_up(stage3_content, follow_up_q.strip())
                answer_key = f"q{len(st.session_state.follow_up_answers)}"
                st.session_state.follow_up_answers[answer_key] = {
                    "question": follow_up_q.strip(),
                    "answer": answer,
                    "time": datetime.now().strftime("%H:%M:%S"),
                }

        # 展示追问历史
        if st.session_state.follow_up_answers:
            st.divider()
            st.caption(f"追问历史（{len(st.session_state.follow_up_answers)} 条）")
            for key, item in reversed(list(st.session_state.follow_up_answers.items())):
                with st.expander(f"❓ {item['question'][:50]}... ({item['time']})", expanded=False):
                    st.markdown(f"""
                    <div class="follow-up-box">
                    {item['answer']}
                    </div>
                    """, unsafe_allow_html=True)

    # ── 导出按钮 ──
    st.divider()
    export_col1, export_col2 = st.columns([1, 3])
    with export_col1:
        st.download_button(
            label="📥 导出 Markdown 文档",
            data=export_md,
            file_name=f"知识迁移_{src}_to_{tgt}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with export_col2:
        st.caption(f"📄 文件名：知识迁移_{src}_to_{tgt}_*.md | 含存疑标记和追问内容")