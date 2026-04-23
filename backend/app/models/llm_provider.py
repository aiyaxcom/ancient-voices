"""
LLM Provider 配置模型
用于管理不同的 LLM API 提供商配置
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base
from app.core.timezone import get_cst_now_no_tz


class LLMProvider(Base):
    """LLM 提供商配置表"""
    __tablename__ = "llm_providers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_key = Column(String(64), unique=True, nullable=False, index=True, comment="提供商标识")
    display_name = Column(String(128), nullable=False, comment="显示名称")
    api_url = Column(String(255), nullable=False, comment="API 地址")
    api_key = Column(Text, nullable=False, comment="API Key")
    default_model = Column(String(64), nullable=False, comment="默认模型名称")
    config_json = Column(JSONB, nullable=True, default={}, comment="其他配置参数")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    priority = Column(Integer, default=0, comment="优先级")
    description = Column(Text, nullable=True, comment="描述说明")
    created_at = Column(DateTime, default=get_cst_now_no_tz, comment="创建时间")
    updated_at = Column(DateTime, default=get_cst_now_no_tz, onupdate=get_cst_now_no_tz, comment="更新时间")

    __table_args__ = (
        Index('idx_llm_provider_enabled_priority', 'is_enabled', 'priority'),
    )