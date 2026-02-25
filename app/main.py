from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import get_settings
from app.services.alerts import AlertService
from app.services.analytics import AnalyticsService
from app.services.benchmark import BenchmarkService
from app.services.db_store import DBStore
from app.services.evaluator import EvaluatorService
from app.services.gate import EvalGateService
from app.services.model_registry import ModelRegistry
from app.services.run_store import RunStore
from app.services.task_recommender import TaskRecommender

STATIC_DIR = Path(__file__).resolve().parent / "static"


class ConnectionManager:
    """Manages WebSocket connections for real-time dashboard updates."""
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, data: dict):
        disconnected = []
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws)


ws_manager = ConnectionManager()


def create_app() -> FastAPI:
    settings = get_settings()
    registry = ModelRegistry(settings=settings)
    run_store = RunStore(artifact_dir=settings.run_artifacts_path)
    analytics = AnalyticsService(run_store=run_store)
    evaluator = EvaluatorService(registry=registry, run_store=run_store)
    eval_gate = EvalGateService()
    alerts = AlertService(settings=settings)
    db_store = DBStore(database_url=settings.database_url)
    db_store.init_schema()  # idempotent CREATE IF NOT EXISTS
    benchmark_service = BenchmarkService(
        benchmarks_dir=settings.benchmarks_dir, evaluator=evaluator
    )
    task_recommender = TaskRecommender(
        tasks_path=settings.tasks_path,
        registry=registry,
        benchmark_service=benchmark_service,
    )

    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.state.settings = settings
    app.state.registry = registry
    app.state.evaluator = evaluator
    app.state.analytics = analytics
    app.state.eval_gate = eval_gate
    app.state.alerts = alerts
    app.state.db_store = db_store
    app.state.ws_manager = ws_manager
    app.state.benchmark_service = benchmark_service
    app.state.task_recommender = task_recommender
    app.include_router(router, prefix="/api/v1", tags=["evaluation"])

    # Dashboard route
    @app.get("/dashboard", response_class=HTMLResponse, tags=["dashboard"])
    async def dashboard():
        html_path = STATIC_DIR / "dashboard.html"
        return HTMLResponse(content=html_path.read_text(), status_code=200)

    # WebSocket endpoint for real-time updates
    @app.websocket("/ws/live")
    async def websocket_endpoint(websocket: WebSocket):
        await ws_manager.connect(websocket)
        try:
            while True:
                await websocket.receive_text()  # Keep connection alive
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)

    # Static assets
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    return app


app = create_app()

