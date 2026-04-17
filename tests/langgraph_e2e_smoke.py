from __future__ import annotations

import shutil
from pathlib import Path

from ainovel_py.agents.build import build_tool_registry
from ainovel_py.agents.orchestrator.langgraph.core import LangGraphRuntime
from ainovel_py.bootstrap.config import Config, ProviderConfig
from ainovel_py.domain.runtime import Phase, Progress
from ainovel_py.domain.story import OutlineEntry
from ainovel_py.store.store import Store


TEST_DIR = Path("output/langgraph_e2e_smoke")


class _StubClient:
    def complete(self, system_prompt, user_prompt, temperature=0.0):
        return '{"summary":"第1章总结","characters":["主角"],"key_events":["主角觉醒"],"timeline_events":[],"foreshadow_updates":[],"relationship_changes":[],"state_changes":[],"hook_type":"mystery","dominant_strand":"quest"}'


class StubLangGraphRuntime(LangGraphRuntime):
    def build_client(self):
        return _StubClient()

    def _generate_chapter_with_context(self, client, seed_text, chapter, context, plan, contract):
        return (f"第{chapter}章正文：主角在雨夜推进剧情，并在结尾留下悬念。", 26)

    def _summarize_chapter(self, client, chapter, draft):
        return f"第{chapter}章总结"


def _setup_store() -> Store:
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    store = Store(str(TEST_DIR))
    store.init()
    store.progress.save(
        Progress(
            novel_name="测试小说",
            phase=Phase.WRITING,
            current_chapter=1,
            total_chapters=1,
            completed_chapters=[],
            total_word_count=0,
        )
    )
    store.outline.save_premise("# 测试小说\n一个主角在雨夜卷入阴谋的故事。")
    store.outline.save_outline([
        OutlineEntry(chapter=1, title="雨夜觉醒", core_event="主角觉醒力量", hook="更大阴谋浮现", scenes=["雨夜", "觉醒", "逃离"])
    ])
    return store


def main() -> int:
    store = _setup_store()
    cfg = Config(
        output_dir=str(TEST_DIR),
        provider="openai",
        model="gpt-4o-mini",
        providers={"openai": ProviderConfig(api_key="test-key")},
        style="default",
        context_window=128000,
        orchestrator="langgraph",
    )
    runner = type("Runner", (), {"call_tool": lambda self, name, args: build_tool_registry(store)[name].execute(args)})()
    runtime = StubLangGraphRuntime(cfg, runner, store, lambda event: None, lambda channel, delta: None)
    runtime.start("测试剧情：主角在雨夜觉醒并卷入阴谋。")

    progress = store.progress.load()
    if progress is None or 1 not in progress.completed_chapters:
        raise RuntimeError("chapter 1 was not committed")
    chapter_text = store.drafts.load_chapter_text(1)
    if not chapter_text:
        raise RuntimeError("final chapter text missing")
    summary = store.summaries.load_summary(1)
    if summary is None:
        raise RuntimeError("chapter summary missing")
    checkpoint = store.checkpoints.latest_global()
    if checkpoint is None or checkpoint.step != "commit":
        raise RuntimeError("commit checkpoint missing")

    print("langgraph_e2e_smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
