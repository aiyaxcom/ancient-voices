"""
FastAPI 应用入口（Ancient Voices - 开源版本）
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.wenyan import router as wenyan_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    logger.info("初始化数据库...")
    await init_db()
    logger.info("数据库初始化完成")

    yield

    # 关闭时清理资源
    await close_db()
    logger.info("应用已关闭")


app = FastAPI(
    title="Ancient Voices",
    description="历史人物沉浸式对话系统",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"全局异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误"},
    )


# 注册路由
app.include_router(wenyan_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Ancient Voices API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}