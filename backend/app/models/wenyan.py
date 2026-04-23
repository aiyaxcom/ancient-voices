"""
文言文深度共情教学智能体 - 数据库模型（开源简化版本）
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.timezone import get_cst_now_no_tz


class WenyanScenario(Base):
    """场景表（如《鸿门宴》）"""
    __tablename__ = "wenyan_scenarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(128), nullable=False, comment="场景标题")
    source_work = Column(String(128), nullable=True, comment="出处（如《史记·项羽本纪》）")
    description = Column(Text, nullable=True, comment="场景描述")
    context_json = Column(JSONB, nullable=True, comment="背景知识库（原文、译文、注释）")
    era_year = Column(Integer, nullable=True, comment="历史年份（负数为公元前）")
    era_name = Column(String(32), nullable=True, comment="年代名称（如春秋、战国、三国）")
    is_official = Column(Boolean, default=False, comment="是否为官方预设场景")
    status = Column(String(32), default="active", comment="状态：active/draft/archived")
    created_at = Column(DateTime, default=get_cst_now_no_tz, comment="创建时间")
    updated_at = Column(DateTime, default=get_cst_now_no_tz, onupdate=get_cst_now_no_tz, comment="更新时间")

    # 关联关系
    agents = relationship("WenyanAgent", back_populates="scenario", cascade="all, delete-orphan")
    sessions = relationship("WenyanSession", back_populates="scenario", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_wenyan_scenario_status", "status"),
        Index("idx_wenyan_scenario_official", "is_official"),
        Index("idx_wenyan_scenario_era", "era_year"),
    )


class WenyanAgent(Base):
    """智能体角色表"""
    __tablename__ = "wenyan_agents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id = Column(Integer, ForeignKey("wenyan_scenarios.id"), nullable=False, comment="所属场景")
    name = Column(String(64), nullable=False, comment="角色名称")
    personality = Column(Text, nullable=False, comment="核心性格描述")
    goal = Column(Text, nullable=False, comment="角色目标")
    known_info = Column(JSONB, default=list, comment="已知信息列表")
    unknown_info = Column(JSONB, default=list, comment="未知信息列表")
    speech_style = Column(Text, nullable=True, comment="说话风格描述")
    knowledge_base = Column(JSONB, default=dict, comment="专属知识库")
    system_prompt = Column(Text, nullable=True, comment="系统提示词（自动生成）")
    avatar_url = Column(String(255), nullable=True, comment="角色头像")
    sort_order = Column(Integer, default=0, comment="排序")
    created_at = Column(DateTime, default=get_cst_now_no_tz, comment="创建时间")

    # 关联关系
    scenario = relationship("WenyanScenario", back_populates="agents")
    sessions = relationship("WenyanSession", back_populates="target_agent")
    messages = relationship("WenyanMessage", back_populates="agent")
    reports = relationship("WenyanReport", back_populates="agent")

    __table_args__ = (
        Index("idx_wenyan_agent_scenario", "scenario_id"),
    )


class WenyanSession(Base):
    """对话会话表（无需用户系统）"""
    __tablename__ = "wenyan_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id = Column(Integer, ForeignKey("wenyan_scenarios.id"), nullable=False, comment="场景 ID")
    mode = Column(String(32), nullable=False, comment="模式：interview/conflict/strategist")
    user_role = Column(String(64), nullable=True, comment="用户扮演的角色（conflict 模式）")
    target_agent_id = Column(Integer, ForeignKey("wenyan_agents.id"), nullable=True, comment="对话对象")
    status = Column(String(32), default="active", comment="状态：active/completed/archived")
    created_at = Column(DateTime, default=get_cst_now_no_tz, comment="创建时间")
    updated_at = Column(DateTime, default=get_cst_now_no_tz, onupdate=get_cst_now_no_tz, comment="更新时间")
    ended_at = Column(DateTime, nullable=True, comment="结束时间")

    # 关联关系
    scenario = relationship("WenyanScenario", back_populates="sessions")
    target_agent = relationship("WenyanAgent", back_populates="sessions")
    messages = relationship("WenyanMessage", back_populates="session", cascade="all, delete-orphan")
    reports = relationship("WenyanReport", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_wenyan_session_status", "status"),
    )


class WenyanMessage(Base):
    """对话消息表"""
    __tablename__ = "wenyan_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("wenyan_sessions.id"), nullable=False, comment="会话 ID")
    role = Column(String(32), nullable=False, comment="角色：user/agent/system")
    agent_id = Column(Integer, ForeignKey("wenyan_agents.id"), nullable=True, comment="发言的智能体")
    content = Column(Text, nullable=False, comment="消息内容")
    message_metadata = Column(JSONB, default=dict, comment="元数据（情绪标签、策略建议等）")
    created_at = Column(DateTime, default=get_cst_now_no_tz, comment="创建时间")

    # 关联关系
    session = relationship("WenyanSession", back_populates="messages")
    agent = relationship("WenyanAgent", back_populates="messages")

    __table_args__ = (
        Index("idx_wenyan_message_session", "session_id"),
    )


class WenyanReport(Base):
    """反思报告表（无需用户系统）"""
    __tablename__ = "wenyan_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("wenyan_sessions.id"), nullable=False, comment="会话 ID")
    agent_id = Column(Integer, ForeignKey("wenyan_agents.id"), nullable=True, comment="分析的角色")
    status = Column(String(32), nullable=False, default="pending", comment="状态: pending/processing/completed/failed")
    report_content = Column(Text, nullable=True, comment="AI 生成的反思报告")
    core_dilemma = Column(Text, nullable=True, comment="核心困境提炼")
    decision_logic = Column(Text, nullable=True, comment="决策逻辑分析")
    emotional_analysis = Column(Text, nullable=True, comment="情感深度解读")
    historical_context = Column(Text, nullable=True, comment="历史背景关联")
    reflection_questions = Column(JSONB, nullable=True, comment="反思问题列表")
    error_message = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(DateTime, default=get_cst_now_no_tz, comment="创建时间")
    updated_at = Column(DateTime, default=get_cst_now_no_tz, onupdate=get_cst_now_no_tz, comment="更新时间")

    # 关联关系
    session = relationship("WenyanSession", back_populates="reports")
    agent = relationship("WenyanAgent", back_populates="reports")

    __table_args__ = (
        Index("idx_wenyan_report_session", "session_id"),
        Index("idx_wenyan_report_status", "status"),
    )