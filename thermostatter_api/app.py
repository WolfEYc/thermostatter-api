from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager

import thermostatter_api
from thermostatter_api import telemetry
from thermostatter_api.logger import LOGGER


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    telemetry.shutdown_telemetry()


app = FastAPI(version=thermostatter_api.version, lifespan=lifespan)

telemetry.setup_telemetry(app)


@app.get("/hello-world")
def hello_world_endpoint():
    LOGGER.info("hello, logs!")
    return "Hello, World!"


@app.get("/ping")
def big_burrito_endpoint(msg: str):
    LOGGER.info(f"echo: {msg}")
    return "pong"
