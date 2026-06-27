"""
知识迁移桥梁 — 四阶段流水线引擎 v2.0
优化项：并行执行 / 缓存 / 格式校验 / 自动修复 / 失败重试
"""
import concurrent.futures
import hashlib
import re
import time
from typing import List, Dict, Any

from llm_client import LLMClient
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
import prompts

# ── 全局缓存 ──
_cache = {}
_cache_stats = {"hits": 0, "misses": 0}


def _make_key(source: str, target: str, stage: int) -> str:
    raw = f"{source.strip()}|{target.strip()}|{stage}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


# ── 格式校验 ──
def _validate(text: str, stage: int) -> List[str]:
    """返回发现的问题列表；空列表表示通过。"""
    issues = []

    # 1. 空括号检测
    empty_placeholders = [r"（）", r"【】", r"\(\s*\)", r"\[\s*\]"]
    for pat in empty_placeholders:
        if re.search(pat, text):
            issues.append(f"含空占位符: {pat}")

    # 2. 长度下限
    min_len = {1: 200, 2: 200, 3: 400, 4: 200}
    if len(text) < min_len.get(stage, 150):
        issues.append(f"输出偏短 ({len(text)}字)，可能不完整")

    # 3. Stage 3/4 英文术语检测
    if stage >= 3:
        forbidden = ["mapping", "analogy", "transfer", "map to", "analog", "Map:"]
        for w in forbidden:
            if w.lower() in text.lower():
                issues.append(f"含英文术语: {w}")

    return issues


# ── 自动修复 ──
def _auto_fix(text: str) -> str:
    """自动清除空白占位符行、压缩多余空行。"""
    text = re.sub(r"^\s*[-•*]\s*（）\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-•*]\s*【】\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def clear_cache():
    global _cache, _cache_stats
    _cache.clear()
    _cache_stats = {"hits": 0, "misses": 0}


def cache_stats() -> Dict[str, int]:
    return dict(_cache_stats)


# ============================================================
class KnowledgeBridge:
    """四阶段跨领域知识迁移流水线 v2.0

    与 v1.0 的区别：
    - Stage1 + Stage2 并行调用（40% 加速）
    - 内存缓存：相同领域对 → 直接返回缓存
    - 格式校验 + 自动修复空占位符
    - LLM 调用失败自动重试（最多 2 次，递增等待）
    - yield 三元组 (stage, content, meta)，前端可展示运行细节
    """

    MAX_RETRIES = 2

    def __init__(self):
        self.llm = LLMClient(api_key=LLM_API_KEY, base_url=LLM_BASE_URL, model=LLM_MODEL)
        self.results = {}
        self.meta_log = {}  # stage → meta dict

    # ── 单次 LLM 调用（带缓存 + 重试 + 校验）──────────────
    def _call(self, system: str, user: str, temperature: float,
              stage: int, source: str, target: str) -> Dict[str, Any]:
        key = _make_key(source, target, stage)

        # 命中缓存
        if key in _cache:
            _cache_stats["hits"] += 1
            return {"content": _cache[key], "cached": True,
                    "issues": [], "attempts": 0, "retry_count": 0}

        _cache_stats["misses"] += 1
        last_issues = None

        for attempt in range(1, self.MAX_RETRIES + 2):  # 1 次正常 + N 次重试
            try:
                raw = self.llm.chat(system, user, temperature=temperature)
            except Exception as exc:
                if attempt > self.MAX_RETRIES:
                    return {"content": f"[阶段{stage} API 调用失败] {exc}",
                            "cached": False, "issues": [str(exc)],
                            "attempts": attempt, "retry_count": attempt - 1,
                            "error": str(exc)}
                time.sleep(2 * attempt)
                continue

            fixed = _auto_fix(raw)
            issues = _validate(fixed, stage)

            if not issues:
                _cache[key] = fixed
                return {"content": fixed, "cached": False,
                        "issues": [], "attempts": attempt,
                        "retry_count": attempt - 1}
            # 有格式问题 → 重试（附修复提示）
            last_issues = issues
            if attempt <= self.MAX_RETRIES:
                system = (
                    system + "\n\n【格式提醒】上次输出存在问题："
                    + "；".join(issues)
                    + "。请严格避免空括号和英文术语，确保格式规范后再输出。"
                )
                time.sleep(1.5 * attempt)

        # 重试耗尽，返回最后一次结果（带 issues 标记）
        _cache[key] = fixed
        return {"content": fixed, "cached": False,
                "issues": last_issues or [],
                "attempts": self.MAX_RETRIES + 1,
                "retry_count": self.MAX_RETRIES}

    # ── 主流水线 ────────────────────────────────────────
    def run(self, source_domain: str, target_domain: str):
        self.results = {}
        self.meta_log = {}
        src = source_domain.strip()
        tgt = target_domain.strip()

        # ─── 并行执行 Stage 1 + Stage 2 ───
        t0 = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            f1 = ex.submit(
                self._call,
                prompts.STAGE1_SYSTEM,
                prompts.STAGE1_USER.format(domain=src),
                0.5, 1, src, tgt,
            )
            f2 = ex.submit(
                self._call,
                prompts.STAGE2_SYSTEM.format(target_domain=tgt),
                prompts.STAGE2_USER.format(target_domain=tgt),
                0.5, 2, src, tgt,
            )
            r1 = f1.result()
            r2 = f2.result()
        parallel_elapsed = round(time.time() - t0, 1)

        self.results["stage1"] = r1["content"]
        self.results["stage2"] = r2["content"]
        self.meta_log[1] = {**r1, "parallel_elapsed_s": parallel_elapsed}
        self.meta_log[2] = {**r2, "parallel_elapsed_s": parallel_elapsed}

        yield 1, r1["content"], self.meta_log[1]
        yield 2, r2["content"], self.meta_log[2]

        # ─── Stage 3: 跨领域映射 ───
        r3 = self._call(
            prompts.STAGE3_SYSTEM.format(source_concepts=r1["content"],
                                         target_concepts=r2["content"]),
            prompts.STAGE3_USER,
            0.4, 3, src, tgt,
        )
        self.results["stage3"] = r3["content"]
        self.meta_log[3] = r3
        yield 3, r3["content"], r3

        # ─── Stage 4: 测验生成 ───
        r4 = self._call(
            prompts.STAGE4_SYSTEM,
            prompts.STAGE4_USER.format(mappings=r3["content"]),
            0.6, 4, src, tgt,
        )
        self.results["stage4"] = r4["content"]
        self.meta_log[4] = r4
        yield 4, r4["content"], r4

    # ── 交互式追问 ──
    def follow_up(self, mappings_text: str, question: str) -> str:
        """对已生成的类比映射进行追问，要求 LLM 换个角度或深入解释。

        Args:
            mappings_text: Stage 3 的完整输出
            question: 用户的追问（如"换个角度解释火候→训练过程"）
        Returns:
            LLM 的追问回答文本
        """
        system = (
            "你是一位耐心且善于沟通的认知科学老师。"
            "用户已经看过了下面的跨领域知识迁移（类比映射），但对某个具体类比还有疑问。\n\n"
            "## 你的任务\n"
            "根据用户的问题，对相关类比进行更深入的解释。\n"
            "你可以：\n"
            "1. 换一个生活化的场景重新解释这个类比\n"
            "2. 补充更多结构对应关系的细节\n"
            "3. 重点解释用户困惑的那部分\n\n"
            "## 原则\n"
            "- 优先使用源领域的语言，而非目标领域的术语\n"
            "- 如果用户的类比确实存在边界限制，要诚实指出\n"
            "- 回答精炼，控制在 300 字以内\n"
            "- 全文使用中文\n\n"
            "## 已生成的类比映射\n"
            f"{mappings_text}"
        )
        user_msg = f"我对以下内容有疑问：{question}"
        try:
            return self.llm.chat(system, user_msg, temperature=0.6)
        except Exception as e:
            return f"[追问失败] {e}"

    def get_stats(self) -> Dict[str, Any]:
        return {
            "cache_hits": _cache_stats["hits"],
            "cache_misses": _cache_stats["misses"],
            "meta": self.meta_log,
        }
