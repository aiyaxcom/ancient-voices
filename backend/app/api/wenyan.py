"""
Ancient Voices - API 路由（简化版本）

历史人物沉浸式对话系统，无需用户认证
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from loguru import logger
import httpx
import json

from app.core.database import get_db, async_session_maker
from app.models.wenyan import (
    WenyanScenario, WenyanAgent, WenyanSession, WenyanMessage, WenyanReport
)
from app.models.llm_provider import LLMProvider
from app.schemas.wenyan import (
    WenyanScenarioCreate, WenyanScenarioResponse, WenyanScenarioBrief,
    WenyanScenarioListResponse,
    WenyanAgentCreate, WenyanAgentResponse, WenyanAgentBrief,
    WenyanSessionCreate, WenyanSessionResponse, WenyanSessionListResponse,
    WenyanChatRequest, WenyanChatResponse,
    WenyanMessageResponse, WenyanMessageListResponse,
    WenyanReportRequest, WenyanReportCreateResponse, WenyanReportResponse,
    WenyanReportBrief, WenyanReportListResponse,
    WenyanAnalyzeRequest, WenyanAnalyzeResponse,
    WenyanCreateSaveRequest, WenyanCreateSaveResponse,
)

router = APIRouter(prefix="/wenyan", tags=["历史人物对话"])


async def get_active_llm_provider(db: AsyncSession) -> LLMProvider:
    """获取当前启用的 LLM 提供商"""
    result = await db.execute(
        select(LLMProvider)
        .where(LLMProvider.is_enabled == True)
        .order_by(LLMProvider.priority.desc())
        .limit(1)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=500, detail="未配置 LLM 提供商")
    return provider


def generate_system_prompt(agent: WenyanAgent, scenario: WenyanScenario) -> str:
    """生成角色系统提示词"""
    known_info = agent.known_info or []
    unknown_info = agent.unknown_info or []

    known_text = "\n".join([f"- {info}" for info in known_info]) if known_info else "无特殊限制"
    unknown_text = "\n".join([f"- {info}" for info in unknown_info]) if unknown_info else "无"

    return f"""你是{agent.name}，来自《{scenario.source_work or '历史记载'}》。

时间：{scenario.title}当日。

【性格】
{agent.personality}

【目标】
{agent.goal}

【已知信息】
{known_text}

【未知信息】
{agent.name}不知道以下事情：
{unknown_text}

【说话风格】
{agent.speech_style or '符合身份的文言风格'}

规则：
1. 只基于历史记载和你的人物设定回应
2. 保持角色一致性
3. 回答要有深度，体现内心挣扎
4. 回答不超过200字"""


async def call_llm(system_prompt: str, messages: list, db: AsyncSession) -> str:
    """调用 LLM"""
    provider = await get_active_llm_provider(db)

    llm_messages = [{"role": "system", "content": system_prompt}] + messages

    config = provider.config_json or {}

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{provider.api_url}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {provider.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": provider.default_model,
                "messages": llm_messages,
                "temperature": config.get("temperature", 0.7),
                "max_tokens": config.get("max_tokens", 500),
            }
        )
        if resp.status_code != 200:
            raise Exception("LLM API 调用失败")
        result = resp.json()
        return result.get("choices", [{}])[0].get("message", {}).get("content", "")


# ============ 场景管理 ============

@router.get("/scenarios", response_model=WenyanScenarioListResponse)
async def list_scenarios(db: AsyncSession = Depends(get_db)):
    """获取场景列表"""
    result = await db.execute(
        select(WenyanScenario)
        .where(WenyanScenario.status == "active")
        .order_by(WenyanScenario.era_year.asc().nullslast())
    )
    scenarios = result.scalars().all()

    briefs = []
    for s in scenarios:
        count_result = await db.execute(
            select(func.count(WenyanAgent.id)).where(WenyanAgent.scenario_id == s.id)
        )
        agent_count = count_result.scalar() or 0
        briefs.append(WenyanScenarioBrief(
            id=s.id, title=s.title, source_work=s.source_work,
            description=s.description, era_year=s.era_year, era_name=s.era_name,
            is_official=s.is_official, agent_count=agent_count,
        ))

    return WenyanScenarioListResponse(
        official=[b for b in briefs if b.is_official],
        user_created=[b for b in briefs if not b.is_official],
        total=len(briefs),
    )


@router.get("/scenarios/{scenario_id}", response_model=WenyanScenarioResponse)
async def get_scenario(scenario_id: int, db: AsyncSession = Depends(get_db)):
    """获取场景详情"""
    result = await db.execute(
        select(WenyanScenario).where(WenyanScenario.id == scenario_id)
    )
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    agents_result = await db.execute(
        select(WenyanAgent).where(WenyanAgent.scenario_id == scenario_id)
        .order_by(WenyanAgent.sort_order)
    )
    agents = agents_result.scalars().all()

    return WenyanScenarioResponse(
        id=scenario.id, title=scenario.title, source_work=scenario.source_work,
        description=scenario.description, context_json=scenario.context_json,
        era_year=scenario.era_year, era_name=scenario.era_name,
        is_official=scenario.is_official, creator_id=None, status=scenario.status,
        created_at=scenario.created_at, updated_at=scenario.updated_at,
        agents=[WenyanAgentBrief(
            id=a.id, name=a.name, personality=a.personality, goal=a.goal,
            avatar_url=a.avatar_url
        ) for a in agents],
    )


# ============ 会话管理 ============

@router.post("/sessions", response_model=WenyanSessionResponse)
async def create_session(data: WenyanSessionCreate, db: AsyncSession = Depends(get_db)):
    """创建会话"""
    scenario_result = await db.execute(
        select(WenyanScenario).where(WenyanScenario.id == data.scenario_id)
    )
    scenario = scenario_result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    target_agent = None
    if data.target_agent_id:
        agent_result = await db.execute(
            select(WenyanAgent).where(WenyanAgent.id == data.target_agent_id)
        )
        target_agent = agent_result.scalar_one_or_none()

    session = WenyanSession(
        scenario_id=data.scenario_id, mode=data.mode,
        user_role=data.user_role, target_agent_id=data.target_agent_id,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)

    return WenyanSessionResponse(
        id=session.id, user_id=0, scenario_id=session.scenario_id,
        scenario_title=scenario.title, mode=session.mode, user_role=session.user_role,
        target_agent_id=session.target_agent_id,
        target_agent=WenyanAgentBrief(
            id=target_agent.id, name=target_agent.name,
            personality=target_agent.personality, goal=target_agent.goal,
            avatar_url=target_agent.avatar_url
        ) if target_agent else None,
        status=session.status, created_at=session.created_at, message_count=0,
    )


@router.get("/sessions/{session_id}", response_model=WenyanSessionResponse)
async def get_session(session_id: int, db: AsyncSession = Depends(get_db)):
    """获取会话详情"""
    result = await db.execute(
        select(WenyanSession).where(WenyanSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    scenario_result = await db.execute(
        select(WenyanScenario).where(WenyanScenario.id == session.scenario_id)
    )
    scenario = scenario_result.scalar_one_or_none()

    target_agent = None
    if session.target_agent_id:
        agent_result = await db.execute(
            select(WenyanAgent).where(WenyanAgent.id == session.target_agent_id)
        )
        target_agent = agent_result.scalar_one_or_none()

    count_result = await db.execute(
        select(func.count(WenyanMessage.id)).where(WenyanMessage.session_id == session_id)
    )
    message_count = count_result.scalar() or 0

    return WenyanSessionResponse(
        id=session.id, user_id=0, scenario_id=session.scenario_id,
        scenario_title=scenario.title if scenario else None,
        mode=session.mode, user_role=session.user_role,
        target_agent_id=session.target_agent_id,
        target_agent=WenyanAgentBrief(
            id=target_agent.id, name=target_agent.name,
            personality=target_agent.personality, goal=target_agent.goal,
            avatar_url=target_agent.avatar_url
        ) if target_agent else None,
        status=session.status, created_at=session.created_at, message_count=message_count,
    )


# ============ 对话 ============

@router.get("/sessions/{session_id}/messages", response_model=WenyanMessageListResponse)
async def get_messages(session_id: int, db: AsyncSession = Depends(get_db)):
    """获取消息历史"""
    session_result = await db.execute(
        select(WenyanSession).where(WenyanSession.id == session_id)
    )
    if not session_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="会话不存在")

    messages_result = await db.execute(
        select(WenyanMessage).where(WenyanMessage.session_id == session_id)
        .order_by(WenyanMessage.created_at)
    )
    messages = messages_result.scalars().all()

    return WenyanMessageListResponse(
        messages=[WenyanMessageResponse(
            id=m.id, session_id=m.session_id, role=m.role,
            agent_id=m.agent_id, agent_name=None, content=m.content,
            message_metadata=m.message_metadata, created_at=m.created_at,
        ) for m in messages],
        total=len(messages),
    )


@router.post("/sessions/{session_id}/chat", response_model=WenyanChatResponse)
async def send_chat(session_id: int, data: WenyanChatRequest, db: AsyncSession = Depends(get_db)):
    """发送消息"""
    session_result = await db.execute(
        select(WenyanSession).where(WenyanSession.id == session_id)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    scenario_result = await db.execute(
        select(WenyanScenario).where(WenyanScenario.id == session.scenario_id)
    )
    scenario = scenario_result.scalar_one_or_none()

    agent_result = await db.execute(
        select(WenyanAgent).where(WenyanAgent.id == session.target_agent_id)
    )
    agent = agent_result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 保存用户消息
    user_msg = WenyanMessage(session_id=session_id, role="user", content=data.message)
    db.add(user_msg)

    # 获取历史消息
    history_result = await db.execute(
        select(WenyanMessage).where(WenyanMessage.session_id == session_id)
        .order_by(WenyanMessage.created_at)
    )
    history = history_result.scalars().all()

    llm_messages = [{"role": m.role, "content": m.content} for m in history]
    llm_messages.append({"role": "user", "content": data.message})

    system_prompt = generate_system_prompt(agent, scenario)
    response_content = await call_llm(system_prompt, llm_messages, db)

    # 保存角色回复
    agent_msg = WenyanMessage(session_id=session_id, role="agent", agent_id=agent.id, content=response_content)
    db.add(agent_msg)
    await db.flush()

    return WenyanChatResponse(
        role="agent", agent_id=agent.id, agent_name=agent.name, content=response_content,
    )


# ============ 报告 ============

@router.post("/sessions/{session_id}/reports", response_model=WenyanReportCreateResponse)
async def create_report(session_id: int, data: WenyanReportRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """生成反思报告"""
    session_result = await db.execute(
        select(WenyanSession).where(WenyanSession.id == session_id)
    )
    if not session_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="会话不存在")

    report = WenyanReport(session_id=session_id, agent_id=data.agent_id, status="pending")
    db.add(report)
    await db.flush()
    await db.refresh(report)

    background_tasks.add_task(generate_report_task, report.id)

    return WenyanReportCreateResponse(report_id=report.id, status="pending")


async def generate_report_task(report_id: int):
    """后台生成报告"""
    async with async_session_maker() as db:
        result = await db.execute(select(WenyanReport).where(WenyanReport.id == report_id))
        report = result.scalar_one_or_none()
        if not report:
            return

        report.status = "completed"
        report.report_content = "基于对话分析生成的反思报告"
        report.reflection_questions = ["该角色为什么做出这样的选择？", "如果是你，你会如何处理？"]
        await db.commit()


@router.get("/reports/{report_id}", response_model=WenyanReportResponse)
async def get_report(report_id: int, db: AsyncSession = Depends(get_db)):
    """获取报告详情"""
    result = await db.execute(select(WenyanReport).where(WenyanReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    agent_name = None
    if report.agent_id:
        agent_result = await db.execute(select(WenyanAgent).where(WenyanAgent.id == report.agent_id))
        agent = agent_result.scalar_one_or_none()
        agent_name = agent.name if agent else None

    return WenyanReportResponse(
        id=report.id, session_id=report.session_id, agent_id=report.agent_id,
        agent_name=agent_name, status=report.status, report_content=report.report_content,
        reflection_questions=report.reflection_questions, created_at=report.created_at,
    )


# ============ 场景创建 ============

@router.post("/scenarios/create", response_model=WenyanCreateSaveResponse)
async def save_scenario(data: WenyanCreateSaveRequest, db: AsyncSession = Depends(get_db)):
    """保存自定义场景"""
    scenario = WenyanScenario(
        title=data.scenario.title, source_work=data.scenario.source_work,
        description=data.scenario.description, era_year=data.scenario.era_year,
        era_name=data.scenario.era_name, is_official=False, status="active",
    )
    db.add(scenario)
    await db.flush()
    await db.refresh(scenario)

    agent_ids = []
    for agent_data in data.agents:
        agent = WenyanAgent(
            scenario_id=scenario.id, name=agent_data.name,
            personality=agent_data.personality, goal=agent_data.goal,
            known_info=agent_data.known_info, unknown_info=agent_data.unknown_info,
            speech_style=agent_data.speech_style,
        )
        db.add(agent)
        await db.flush()
        await db.refresh(agent)
        agent_ids.append(agent.id)

    return WenyanCreateSaveResponse(scenario_id=scenario.id, agent_ids=agent_ids)