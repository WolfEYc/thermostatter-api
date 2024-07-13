import importlib.metadata
import os

import uvicorn
from dotenv import load_dotenv

load_dotenv()

APP_ENV = os.environ["APP_ENV"]
PKG_METADATA = importlib.metadata.metadata("thermostatter-api")
author = PKG_METADATA["Author"]
PROJECT_NAME = PKG_METADATA["Name"]
version = PKG_METADATA["Version"]


def main():
    uvicorn.run("thermostatter_api.app:app", host="0.0.0.0", port=8080)
