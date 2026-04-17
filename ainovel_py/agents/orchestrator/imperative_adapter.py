from __future__ import annotations

from ainovel_py.agents.runner import LLMCoordinatorBackend


class ImperativeOrchestrator:
    def __init__(self, backend: LLMCoordinatorBackend) -> None:
        self._backend = backend

    def start(self, prompt: str) -> None:
        self._backend.start(prompt)

    def resume(self, prompt: str) -> None:
        self._backend.resume(prompt)

    def follow_up(self, text: str) -> None:
        self._backend.follow_up(text)

    def abort(self) -> None:
        self._backend.abort()

    def wait_idle(self) -> None:
        self._backend.wait_idle()
