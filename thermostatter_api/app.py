from fastapi import FastAPI

app = FastAPI()


@app.get("/hello-world")
def hello_world_endpoint():
    return "Hello, World!"


@app.get("/hehe-haha")
def hehe_haha_endpoint():
    return "hehe haha!"


@app.get("/buuurito")
def buuurito_endpoint():
    return "burrrito!"
