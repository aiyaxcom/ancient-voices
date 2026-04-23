"""
应用配置管理（开源版本）
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """应用配置"""

    # 基础配置
    APP_ENV: str = "development"
    DEBUG: bool = True
    APP_SECRET: str = "change-this-secret-key"

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库配置（使用 asyncpg 异步驱动）
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/wenyan_db",
        description="PostgreSQL 数据库连接 URL（异步）"
    )
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # JWT 配置
    JWT_SECRET_KEY: str = "change-this-jwt-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7 天

    # CORS 配置
    CORS_ORIGINS: list = Field(
        default=["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:8000"],
        description="允许的 CORS 源列表"
    )

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def is_prod(self) -> bool:
        return self.APP_ENV == "production"

    def validate_production_config(self) -> list:
        """验证生产环境配置是否安全"""
        warnings = []

        if self.is_prod:
            if self.APP_SECRET == "change-this-secret-key":
                warnings.append("APP_SECRET 使用默认值，请配置安全的密钥")

            if self.JWT_SECRET_KEY == "change-this-jwt-secret-key":
                warnings.append("JWT_SECRET_KEY 使用默认值，请配置安全的密钥")

            if len(self.JWT_SECRET_KEY) < 32:
                warnings.append("JWT_SECRET_KEY 长度不足，建议至少 32 字符")

        return warnings


# 全局配置实例
settings = Settings()