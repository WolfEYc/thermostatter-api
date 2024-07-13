from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager

import thermostatter_api
from thermostatter_api import telemetry
from thermostatter_api.logger import LOGGER
from thermostatter_api.pg import PG


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    telemetry.shutdown_telemetry()
    await PG.close()


app = FastAPI(version=thermostatter_api.version, lifespan=lifespan)

telemetry.setup_telemetry(app)


@app.get("/db-test")
async def db_test_endpoint():
    LOGGER.info("testing db!")
    res = await PG.fetch("SELECT * FROM hello_world")
    if res is None:
        return res

    return res.to_dicts()


@app.get("/ping")
def big_burrito_endpoint(msg: str):
    LOGGER.info(f"echo: {msg}")
    return "pong"
