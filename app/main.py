"""FastAPI 主应用"""

import os
import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .database import init_db, async_session
from .routers import auth_router, glm_router, data_router, admin_router, community_router

load_dotenv()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
        logger.info("[STARTUP] init_db 完成")
    except Exception as e:
        logger.error("[STARTUP] init_db 失败: %s\n%s", str(e), traceback.format_exc())
        raise
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
app.include_router(community_router.router, prefix="/api/v1/community", tags=["community"])


@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}


@app.get("/api/v1/debug/db")
async def debug_db():
    """诊断端点：测试数据库连接和所有表是否可查询（无需认证）"""
    from sqlalchemy import text
    result = {"database_url": os.getenv("DATABASE_URL", "default"), "tables": {}, "errors": []}
    try:
        async with async_session() as session:
            # 测试每个表的查询
            tables_to_test = ["users", "profiles", "resources", "paths", "assess_history", "profile_history"]
            for table_name in tables_to_test:
                try:
                    r = await session.execute(text(f"SELECT COUNT(*) FROM `{table_name}`"))
                    count = r.scalar()
                    result["tables"][table_name] = {"exists": True, "count": count}
                except Exception as e:
                    result["tables"][table_name] = {"exists": False, "error": str(e)}
                    result["errors"].append(f"{table_name}: {str(e)}")
    except Exception as e:
        result["errors"].append(f"DB connection failed: {str(e)}")
    return result
