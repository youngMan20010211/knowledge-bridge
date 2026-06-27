import streamlit as st
from datetime import datetime
from pipeline import KnowledgeBridge
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

# ---- page config ----
st.set_page_config(
    page_title="知识迁移桥梁",
    layout="wide",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "知识迁移桥梁 v2.0 — 基于认知科学类比推理的跨领域学习工具",
    },
)

# ---- custom CSS (Chinese-friendly typography) ----
st.markdown("""
<style>
/* 全局字体：优先使用中文字体栈 */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", "Hiragino Sans GB",
                 "WenQuanYi Micro Hei", "Source Han Sans CN", sans-serif;
    font-size: 16px;
    line-height: 1.8;
    color: #1a1a2e;
}

/* 标题样式 */
h1 { font-size: 2rem; font-weight: 700; letter-spacing: 0.05em; color: #0f0f23; }
h2 { font-size: 1.5rem; font-weight: 600; color: #1a1a2e; margin-top: 2rem; }
h3 { font-size: 1.2rem; font-weight: 600; color: #2d2d44; margin-top: 1.5rem; }
h4 { font-size: 1.05rem; font-weight: 500; color: #3d3d5c; }

/* 正文段落 */
p { margin-bottom: 1.2em; text-align: justify; }

/* 主容器 */
.main .block-container {
    max-width: 960px;
    padding: 2rem 3rem;
}

/* 卡片式输入框 */
div[data-testid="stTextInput"] input {
    border: 2px solid #e0e0e8;
    border-radius: 12px;
    padding: 0.75rem 1rem;
    font-size: 1rem;
    transition: border-color 0.3s, box-shadow 0.3s;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #5b5fc7;
    box-shadow: 0 0 0 3px rgba(91, 95, 199, 0.15);
    outline: none;
}

/* 按钮样式 */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #5b5fc7, #6c63ff);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.7rem 2rem;
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    transition: transform 0.15s, box-shadow 0.15s;
}
div[data-testid="stButton"] > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(91, 95, 199, 0.35);
}
div[data-testid="stButton"] > button:active {
    transform: translateY(0);
}

/* 展开卡片样式（结果展示） */
section[data-testid="stExpander"] {
    border: 1px solid #e8e8f0;
    border-radius: 14px;
    margin-bottom: 1rem;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    transition: box-shadow 0.2s;
}
section[data-testid="stExpander"]:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}

/* 展开卡片内部的 markdown */
section[data-testid="stExpander"] .stMarkdown {
    padding: 0.5rem 0;
}

/* 进度条 */
div[data-testid="stProgress"] > div {
    background: linear-gradient(90deg, #5b5fc7, #6c63ff, #8b87ff);
    border-radius: 8px;
}

/* 下载按钮 */
div[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, #2d8c4e, #34a853);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.6rem 1.5rem;
    font-weight: 600;
    transition: transform 0.15s, box-shadow 0.15s;
}
div[data-testid="stDownloadButton"] > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(45, 140, 78, 0.35);
}

/* 侧边栏 */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f8f9fc, #f0f1f8);
}
section[data-testid="stSidebar"] .stMarkdown {
    font-size: 0.9rem;
    line-height: 1.6;
}

/* 表格样式 */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 1rem 0;
    font-size: 0.95rem;
}
th {
    background: #5b5fc7;
    color: white;
    padding: 0.6rem 1rem;
    font-weight: 600;
}
td {
    padding: 0.5rem 1rem;
    border-bottom: 1px solid #e8e8f0;
}
tr:nth-child(even) td {
    background: #f8f9fc;
}

/* 引用块 */
blockquote {
    border-left: 4px solid #6c63ff;
    background: #f5f5ff;
    padding: 0.8rem 1.2rem;
    margin: 1rem 0;
    border-radius: 0 8px 8px 0;
    color: #3d3d5c;
}

/* 分隔线 */
hr { border: none; border-top: 2px solid #e8e8f0; margin: 2.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ---- title ----
st.title("知识迁移桥梁")
st.caption("从你熟悉的领域出发，用类比理解任何新领域 —— 基于认知科学中的结构映射理论")

# ---- sidebar ----
with st.sidebar:
    st.header("API 配置")
    api_key = st.text_input("API Key", type="password", value=LLM_API_KEY)
    base_url = st.text_input("Base URL", value=LLM_BASE_URL)
    model = st.text_input("模型", value=LLM_MODEL)

    st.divider()
    st.header("关于")
    st.markdown(
        """
        **知识迁移桥梁** 基于认知科学中的 **类比推理** 理论，
        通过四阶段 LLM 流水线，将你的已有知识自动映射到陌生领域。

        **四阶段流程：**
        1. 提取源领域概念图谱
        2. 提取目标领域概念图谱
        3. 结构类比映射（含边界标注）
        4. 生成理解检验题

        **核心创新：** 每个类比都必须标注"失效边界"，
        防止过度类比导致的认知偏差。
        """
    )
    st.caption("v2.0 — AI 课程原型")

    st.divider()
    if st.button("刷新页面", use_container_width=True):
        st.rerun()

# ---- session state ----
for key, default in [
    ("results", {}),
    ("running", False),
    ("source_domain", ""),
    ("target_domain", ""),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ---- main input area ----
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

st.divider()

# ---- run button ----
run_col1, run_col2 = st.columns([1, 4])
with run_col1:
    start = st.button("开始知识迁移", type="primary", use_container_width=True)

if start:
    if not source_domain or not target_domain:
        st.warning("请填写两个领域后再开始。")
    elif not api_key:
        st.warning("请在侧边栏填写 API Key。")
    else:
        st.session_state.source_domain = source_domain
        st.session_state.target_domain = target_domain
        st.session_state.results = {}
        st.session_state.running = True

# ---- pipeline execution ----
if st.session_state.running and st.session_state.source_domain:
    bridge = KnowledgeBridge()
    bridge.llm = type(bridge.llm)(
        api_key=api_key, base_url=base_url, model=model
    )

    st.subheader("第二步：知识迁移进行中")
    progress_bar = st.progress(0, text="准备启动...")
    status_area = st.empty()  # 动态刷新区域

    stage_labels = {
        1: "阶段 1/4：提取「{}」核心概念图谱".format(st.session_state.source_domain),
        2: "阶段 2/4：提取「{}」核心概念图谱".format(st.session_state.target_domain),
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

            # ── 实时状态提示 ──
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
                    f"阶段 1+2 并行耗时 {meta.get('parallel_elapsed_s', '?')}s"
                    + status_msg
                )

    except Exception as e:
        st.error(f"流水线严重错误: {e}")
        error_occurred = True
    finally:
        st.session_state.results = all_results
        st.session_state.meta = all_meta
        st.session_state.running = False

    progress_bar.progress(100, text="知识迁移完成！")

    # ── 汇总提示 ──
    stats = bridge.get_stats()
    total_cached = stats["cache_hits"]
    total_retries = sum(
        m.get("retry_count", 0) for m in all_meta.values()
    )

    if error_occurred:
        st.error("部分阶段执行出现问题，请查看下方详情。")
    elif total_cached > 0:
        st.success(
            f"知识迁移完成！⚡ 缓存命中 {total_cached} 次，"
            f"节省了 API 调用。"
        )
    else:
        st.success("四阶段知识迁移已完成，请在下方查看结果。")

    # ── 告警汇总 ──
    if warnings_list:
        with st.expander(f"检测到 {len(warnings_list)} 个格式问题（已自动修复）", expanded=False):
            for w in warnings_list:
                st.warning(w)
    if total_retries > 0:
        st.info(f"本次运行共触发 {total_retries} 次自动重试。")

# ---- results display + export ----
results = st.session_state.results
if results:
    st.divider()

    # header row with title + download button
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.subheader("第三步：查看迁移结果")
    with header_col2:
        # Build export markdown
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        src = st.session_state.source_domain
        tgt = st.session_state.target_domain

        export_md = f"""# 知识迁移报告

> **生成时间**：{timestamp}
> **源领域（用户专长）**：{src}
> **目标领域（学习目标）**：{tgt}

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

> 本报告由「知识迁移桥梁」自动生成 | 基于认知科学类比推理理论
"""
        st.download_button(
            label="导出 Markdown 文档",
            data=export_md,
            file_name=f"知识迁移_{src}_to_{tgt}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    stage_titles = {
        1: f"源领域概念图谱：{st.session_state.source_domain}",
        2: f"目标领域概念图谱：{st.session_state.target_domain}",
        3: "跨领域知识迁移（含边界标注）",
        4: "类比理解检验题",
    }

    for stage_num in range(1, 5):
        if stage_num in results:
            with st.expander(
                f"{stage_titles[stage_num]}",
                expanded=(stage_num == 3),
            ):
                st.markdown(results[stage_num])
