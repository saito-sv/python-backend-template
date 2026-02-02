from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import add_routers
from settings.config import Settings, settings
from task_queue.manage_broker import start_task_broker, stop_task_broker


def create_app(settings: Settings = settings) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        from task_queue.task_broker import broker

        await start_task_broker(broker)
        yield
        await stop_task_broker(broker)

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Add all configured routers
    add_routers(app)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app


# Create app instance for uvicorn
app = create_app()
