import importlib.metadata

import uvicorn

PKG_METADATA = importlib.metadata.metadata("thermostatter-api")
author = PKG_METADATA["Author"]
project = PKG_METADATA["Name"]
version = PKG_METADATA["Version"]


def main():
    uvicorn.run("thermostatter_api.app:app", host="0.0.0.0", port=8080)
