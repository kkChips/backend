"""FastAPI 主应用"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .database import init_db
from .routers import auth_router, glm_router, data_router, admin_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="AI Learning System API", version="1.0.0", lifespan=lifespan)

# CORS 允许的来源：支持环境变量配置多个（逗号分隔）
_default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]
_env_origins = os.getenv("CORS_ORIGIN", "")
if _env_origins:
    _default_origins.extend([o.strip() for o in _env_origins.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(glm_router.router, prefix="/api/v1/glm", tags=["glm"])
app.include_router(data_router.router, prefix="/api/v1/data", tags=["data"])
app.include_router(admin_router.router, prefix="/api/v1/admin", tags=["admin"])


@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}
