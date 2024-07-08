import uvicorn


def main():
    uvicorn.run("thermostatter_api.app:app", host="0.0.0.0", port=8080)
