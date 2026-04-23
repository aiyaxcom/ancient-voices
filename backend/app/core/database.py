"""
数据库配置
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from loguru import logger
from app.core.config import settings
import os

# 创建异步数据库引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# 会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 基类
Base = declarative_base()


async def get_db():
    """获取数据库会话依赖"""
    session = async_session_maker()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_db():
    """初始化数据库：创建所有表"""
    try:
        async with engine.begin() as conn:
            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表创建完成")

        # 检查数据库连接
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("数据库连接正常")

    except Exception as e:
        logger.error(f"数据库初始化失败：{e}")
        raise


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
    logger.info("数据库连接已关闭")