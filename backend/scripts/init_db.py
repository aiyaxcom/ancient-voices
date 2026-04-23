"""
数据库初始化脚本
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, engine
from app.models import *
from loguru import logger


async def main():
    """初始化数据库"""
    logger.info("开始初始化数据库...")

    try:
        await init_db()
        logger.info("数据库初始化成功！")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())