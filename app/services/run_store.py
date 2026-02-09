import json
from datetime import UTC, datetime
from pathlib import Path

from app.schemas.evaluation import RunEvalResponse


class RunStore:
    def __init__(self, artifact_dir: Path) -> None:
        self.artifact_dir = artifact_dir
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

    def save(self, run: RunEvalResponse) -> Path:
        timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{timestamp}_{run.run_id}.json"
        output_path = self.artifact_dir / filename
        output_path.write_text(json.dumps(run.model_dump(), indent=2), encoding="utf-8")
        return output_path
