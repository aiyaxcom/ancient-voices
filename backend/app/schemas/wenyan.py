"""
文言文深度共情教学智能体 - Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============ 场景相关 ============

class WenyanScenarioBase(BaseModel):
    """场景基础信息"""
    title: str = Field(..., max_length=128, description="场景标题")
    source_work: Optional[str] = Field(None, max_length=128, description="出处")
    description: Optional[str] = Field(None, description="场景描述")
    context_json: Optional[dict] = Field(None, description="背景知识库")
    era_year: Optional[int] = Field(None, description="历史年份（负数为公元前）")
    era_name: Optional[str] = Field(None, max_length=32, description="年代名称")


class WenyanScenarioCreate(WenyanScenarioBase):
    """创建场景"""
    pass


class WenyanScenarioResponse(WenyanScenarioBase):
    """场景响应"""
    id: int
    is_official: bool
    creator_id: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    agents: Optional[List["WenyanAgentBrief"]] = None

    model_config = {"from_attributes": True}


class WenyanScenarioBrief(BaseModel):
    """场景简要信息（列表展示）"""
    id: int
    title: str
    source_work: Optional[str] = None
    description: Optional[str] = None
    era_year: Optional[int] = None
    era_name: Optional[str] = None
    is_official: bool
    agent_count: int = 0

    model_config = {"from_attributes": True}


# ============ 智能体角色相关 ============

class WenyanAgentBase(BaseModel):
    """智能体基础信息"""
    name: str = Field(..., max_length=64, description="角色名称")
    personality: str = Field(..., description="核心性格描述")
    goal: str = Field(..., description="角色目标")
    known_info: Optional[List[str]] = Field(default_factory=list, description="已知信息列表")
    unknown_info: Optional[List[str]] = Field(default_factory=list, description="未知信息列表")
    speech_style: Optional[str] = Field(None, description="说话风格描述")
    knowledge_base: Optional[dict] = Field(default_factory=dict, description="专属知识库")
    avatar_url: Optional[str] = Field(None, description="角色头像")


class WenyanAgentCreate(WenyanAgentBase):
    """创建智能体"""
    scenario_id: int = Field(..., description="所属场景 ID")
    sort_order: Optional[int] = Field(0, description="排序")


class WenyanAgentResponse(WenyanAgentBase):
    """智能体响应"""
    id: int
    scenario_id: int
    system_prompt: Optional[str] = None
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class WenyanAgentBrief(BaseModel):
    """智能体简要信息"""
    id: int
    name: str
    personality: str
    goal: str
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}


# ============ 会话相关 ============

class WenyanSessionCreate(BaseModel):
    """创建会话"""
    scenario_id: int = Field(..., description="场景 ID")
    mode: str = Field(..., description="模式：interview/conflict/strategist")
    target_agent_id: Optional[int] = Field(None, description="对话对象")
    user_role: Optional[str] = Field(None, max_length=64, description="用户扮演的角色")


class WenyanSessionResponse(BaseModel):
    """会话响应"""
    id: int
    user_id: int
    scenario_id: int
    scenario_title: Optional[str] = None
    mode: str
    user_role: Optional[str] = None
    target_agent_id: Optional[int] = None
    target_agent: Optional[WenyanAgentBrief] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    message_count: int = 0

    model_config = {"from_attributes": True}


# ============ 消息相关 ============

class WenyanChatRequest(BaseModel):
    """对话请求"""
    session_id: int = Field(..., description="会话 ID")
    message: str = Field(..., min_length=1, max_length=2000, description="用户消息")


class WenyanStrategizeRequest(BaseModel):
    """军师模式请求"""
    session_id: int = Field(..., description="会话 ID")
    agent_id: int = Field(..., description="目标智能体")
    situation: str = Field(..., description="当前场景节点")
    strategy: str = Field(..., min_length=1, max_length=2000, description="策略建议")


class WenyanMessageResponse(BaseModel):
    """消息响应"""
    id: int
    session_id: int
    role: str
    agent_id: Optional[int] = None
    agent_name: Optional[str] = None
    content: str
    message_metadata: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WenyanChatResponse(BaseModel):
    """对话响应"""
    role: str = "agent"
    agent_id: Optional[int] = None
    agent_name: str
    content: str
    metadata: Optional[dict] = None


class WenyanStrategizeResponse(BaseModel):
    """军师模式响应"""
    agent_response: str
    outcome_preview: Optional[str] = None


# ============ 反思报告相关 ============

class WenyanReportRequest(BaseModel):
    """生成反思报告请求"""
    session_id: int = Field(..., description="会话 ID")
    agent_id: Optional[int] = Field(None, description="分析的角色")


class WenyanReportCreateResponse(BaseModel):
    """创建反思报告响应"""
    report_id: int = Field(..., description="报告 ID")
    status: str = Field(..., description="状态")
    message: str = Field(default="报告正在后台生成中")


class WenyanReportResponse(BaseModel):
    """反思报告响应"""
    id: int
    session_id: int
    agent_id: Optional[int] = None
    agent_name: Optional[str] = None
    status: str = Field(default="pending")
    report_content: Optional[str] = None
    core_dilemma: Optional[str] = None
    decision_logic: Optional[str] = None
    emotional_analysis: Optional[str] = None
    historical_context: Optional[str] = None
    reflection_questions: Optional[List[str]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WenyanReportBrief(BaseModel):
    """报告简要信息"""
    id: int
    session_id: int
    agent_id: Optional[int] = None
    agent_name: Optional[str] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WenyanReportListResponse(BaseModel):
    """报告列表响应"""
    reports: List[WenyanReportBrief]
    total: int


# ============ 创建场景相关 ============

class WenyanAnalyzeRequest(BaseModel):
    """分析文言文请求"""
    text: str = Field(..., min_length=50, max_length=10000, description="文言文原文")
    source_work: Optional[str] = Field(None, max_length=128, description="出处")


class WenyanAnalyzeResponse(BaseModel):
    """分析文言文响应"""
    scenario: WenyanScenarioCreate
    agents: List[WenyanAgentCreate]


class WenyanCreateSaveRequest(BaseModel):
    """保存创建的场景"""
    scenario: WenyanScenarioCreate
    agents: List[WenyanAgentCreate]


class WenyanCreateSaveResponse(BaseModel):
    """保存创建场景响应"""
    scenario_id: int
    agent_ids: List[int]


# ============ 列表响应 ============

class WenyanScenarioListResponse(BaseModel):
    """场景列表响应"""
    official: List[WenyanScenarioBrief] = []
    user_created: List[WenyanScenarioBrief] = []
    total: int


class WenyanSessionListResponse(BaseModel):
    """会话列表响应"""
    sessions: List[WenyanSessionResponse]
    total: int


class WenyanMessageListResponse(BaseModel):
    """消息列表响应"""
    messages: List[WenyanMessageResponse]
    total: int


# 更新前向引用
WenyanScenarioResponse.model_rebuild()