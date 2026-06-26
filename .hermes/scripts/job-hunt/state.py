import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

DEFAULT_STATE_PATH = Path(__file__).parent / "state.json"


@dataclass
class State:
    last_run: str | None = None
    prepped_urls: list[str] = field(default_factory=list)

    def is_prepped(self, url: str) -> bool:
        return url in self.prepped_urls

    def mark_prepped(self, url: str) -> None:
        if url not in self.prepped_urls:
            self.prepped_urls.append(url)


class StateStore:
    def __init__(self, path: Path | None = None):
        self.path = path or DEFAULT_STATE_PATH

    def load(self) -> State:
        if not self.path.exists():
            return State()
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except OSError as exc:
            raise RuntimeError(f"I/O error for {self.path}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"I/O error for {self.path}: {exc}") from exc
        return State(**data)

    def save(self, state: State) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise RuntimeError(f"I/O error for {self.path.parent}: {exc}") from exc
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(asdict(state), f, indent=2)
        except OSError as exc:
            raise RuntimeError(f"I/O error for {self.path}: {exc}") from exc
