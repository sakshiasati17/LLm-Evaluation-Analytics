"""RunStore — JSON artifact persistence with in-memory cache to avoid re-reading all files."""

import json
from datetime import UTC, datetime
from pathlib import Path

from app.schemas.evaluation import RunEvalResponse


class RunStore:
    def __init__(self, artifact_dir: Path) -> None:
        self.artifact_dir = artifact_dir
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        # In-memory cache (None = not yet loaded). Invalidated on save.
        self._cache: list[RunEvalResponse] | None = None

    def save(self, run: RunEvalResponse) -> Path:
        timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{timestamp}_{run.run_id}.json"
        output_path = self.artifact_dir / filename
        output_path.write_text(json.dumps(run.model_dump(), indent=2), encoding="utf-8")
        # Prepend to cache to avoid full reload on every write
        if self._cache is not None:
            self._cache.insert(0, run)
        return output_path

    def list_runs(self, limit: int = 200) -> list[RunEvalResponse]:
        if self._cache is None:
            self._cache = self._load_all()
        return self._cache[:limit]

    def invalidate_cache(self) -> None:
        self._cache = None

    def _load_all(self) -> list[RunEvalResponse]:
        runs: list[RunEvalResponse] = []
        for path in sorted(self.artifact_dir.glob("*.json"), reverse=True):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                run = RunEvalResponse.model_validate(payload)
                if not run.created_at:
                    run = run.model_copy(
                        update={"created_at": self._timestamp_from_filename(path.name)}
                    )
                runs.append(run)
            except Exception:  # noqa: BLE001
                # Skip corrupted artifact files rather than crashing the server
                continue
        return runs

    def _timestamp_from_filename(self, filename: str) -> str:
        prefix = filename.split("_", 1)[0]
        try:
            parsed = datetime.strptime(prefix, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
            return parsed.isoformat()
        except ValueError:
            return datetime.now(tz=UTC).isoformat()
