from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def index():
    return {"msg": "Minerva API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080, proxy_headers=True, log_level="debug")
