from contextlib import asynccontextmanager

from app.telemetry import instrument_app, setup_telemetry, shutdown_telemetry

# Must run before the engine and broker are created so they get instrumented.
setup_telemetry()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.config import load  # noqa: E402
from app.routes import add_routers  # noqa: E402
from app.utils.routing.exception_handlers import register_exception_handlers  # noqa: E402
from task_queue.manage_broker import start_task_broker, stop_task_broker  # noqa: E402


def create_app() -> FastAPI:
    cfg = load("app").app

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        from task_queue.task_broker import broker

        await start_task_broker(broker)
        yield
        await stop_task_broker(broker)
        shutdown_telemetry()

    app = FastAPI(title=cfg.name, debug=cfg.debug, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_credentials=cfg.cors_allow_credentials,
        allow_methods=cfg.cors_allow_methods,
        allow_headers=cfg.cors_allow_headers,
    )

    register_exception_handlers(app)
    add_routers(app)
    instrument_app(app)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app


app = create_app()
