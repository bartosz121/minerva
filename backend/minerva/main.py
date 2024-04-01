from fastapi import FastAPI
from starlette.middleware.authentication import AuthenticationMiddleware

from minerva.core.middleware import authentication
from minerva.users.router import router as users_router

app = FastAPI()
app.add_middleware(AuthenticationMiddleware, backend=authentication.AuthenticationBackend())


@app.get("/")
def index():
    return {"msg": "Minerva API"}


app.include_router(users_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080, proxy_headers=True, log_level="debug")
