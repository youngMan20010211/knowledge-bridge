from llm_client import LLMClient
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
import prompts


class KnowledgeBridge:
    """4-stage cross-domain knowledge transfer pipeline."""

    def __init__(self):
        self.llm = LLMClient(
            api_key=LLM_API_KEY, base_url=LLM_BASE_URL, model=LLM_MODEL
        )
        self.results = {}

    def run(self, source_domain: str, target_domain: str):
        """Execute the full 4-stage pipeline. Yields (stage, content) tuples."""
        self.results = {}
        self.source_domain = source_domain
        self.target_domain = target_domain

        # Stage 1
        stage1 = self.llm.chat(
            prompts.STAGE1_SYSTEM, prompts.STAGE1_USER.format(domain=source_domain), temperature=0.5
        )
        self.results["stage1"] = stage1
        yield 1, stage1

        # Stage 2
        stage2 = self.llm.chat(
            prompts.STAGE2_SYSTEM.format(target_domain=target_domain),
            prompts.STAGE2_USER.format(target_domain=target_domain),
            temperature=0.5,
        )
        self.results["stage2"] = stage2
        yield 2, stage2

        # Stage 3 — the critical cross-domain mapping
        stage3 = self.llm.chat(
            prompts.STAGE3_SYSTEM.format(
                source_concepts=stage1, target_concepts=stage2
            ),
            prompts.STAGE3_USER,
            temperature=0.4,
        )
        self.results["stage3"] = stage3
        yield 3, stage3

        # Stage 4 — quiz generation
        stage4 = self.llm.chat(
            prompts.STAGE4_SYSTEM,
            prompts.STAGE4_USER.format(mappings=stage3),
            temperature=0.6,
        )
        self.results["stage4"] = stage4
        yield 4, stage4
