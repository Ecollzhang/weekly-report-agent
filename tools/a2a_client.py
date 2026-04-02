# tools/a2a_client.py
import uuid
import httpx
import logging
from typing import Optional, Dict, Any
from langchain_core.tools import tool
from agents.agent_card import registry, AgentCard

from utils.globalLogger import get_logger
logger = get_logger(__name__)


class A2AClient:
    """A2A 客户端 - 用于调用其他智能体"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
    
    async def call_agent(self, agent_id: str, message: str, context_id: str = "default") -> Optional[str]:
        """调用其他智能体"""
        card = registry.get_card(agent_id)
        if not card:
            logger.error(f"Agent {agent_id} not found in registry")
            return None
        
        return await self._call_agent_card(card, message, context_id)
    
    async def call_agent_by_skill(self, skill_name: str, message: str, context_id: str = "default") -> Optional[str]:
        """根据技能名称调用智能体"""
        agents = registry.discover_by_skill(skill_name)
        if not agents:
            logger.warning(f"No agent found with skill: {skill_name}")
            return None
        
        # 选择第一个匹配的智能体
        return await self._call_agent_card(agents[0], message, context_id)
    
    async def _call_agent_card(self, card: AgentCard, message: str, context_id: str) -> Optional[str]:
        """实际调用智能体"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 构建 A2A 消息
                request_body = {
                    "message": {
                        "messageId": str(uuid.uuid4()),
                        "parts": [{"root": {"text": message, "type": "text"}}],
                        "role": "user"
                    },
                    "context_id": context_id,
                    "task_id": str(uuid.uuid4())
                }
                
                response = await client.post(
                    f"{card.url}/a2a/message",
                    json=request_body
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "completed":
                        for artifact in result.get("artifacts", []):
                            for part in artifact.get("parts", []):
                                if part.get("root", {}).get("text"):
                                    return part["root"]["text"]
                return None
                
        except Exception as e:
            logger.error(f"Failed to call agent {card.agent_id}: {e}")
            return f"Error calling {card.name}: {str(e)}"


# 创建全局客户端
_a2a_client = A2AClient()


# LangChain 工具包装器
@tool
async def call_git_agent(query: str, context_json: str = "{}") -> str:
    """调用 Git Agent 执行 Git 操作，如查看状态、日志、分支等。
    
    Args:
        query: 要询问 Git Agent 的问题，如 "show git status" 或 "commits from last week"
        context: json字符串格式的上下文, 这里必须含有git的工作目录
    
    Returns:
        Git Agent 的响应结果
    """
    query = f"{query}\n\nContext: {context_json}"
    result = await _a2a_client.call_agent("git-agent", query)
    return result or "Git agent 无响应"


@tool
async def call_report_agent(query: str, context_json: str = "{}") -> str:
    """调用 Report Agent 生成报告或摘要。
    
    Args:
        query: 要询问 Report Agent 的问题，如 "generate a report about project" 或 "summarize this"
        context: json字符串格式的上下文, 必须含有生成报告所需的相关信息，如数据来源、报告类型等
    
    Returns:
        Report Agent 的响应结果
    """
    query = f"{query}\n\nContext: {context_json}"
    try:
        result = await _a2a_client.call_agent("report-agent", query)
    except Exception as e:
        logger.error(f"Error calling report agent: {e}")
        return f"Error calling report agent: {str(e)}"
    return result or "Report agent 无响应"

@tool
async def get_agent_skills(agent_id: str) -> str:
    """获取指定智能体的技能列表"""
    card = registry.get_card(agent_id)
    if not card:
        return f"Agent {agent_id} not found"
    
    if card.skills:
        if isinstance(card.skills[0], str):
            return f"{card.name} 的技能: {', '.join(card.skills)}"
        else:
            return f"{card.name} 的技能: {', '.join([s.name for s in card.skills])}"
    else:
        return f"{card.name} 没有公开技能列表"

@tool
async def get_available_agents() -> str:
    """获取当前可用的智能体列表及其能力描述。"""
    agents = registry.list_agents()
    if not agents:
        return "暂无其他可用智能体"
    
    result = "可用智能体列表:\n"
    for card in agents:
        # print(f"Found agent: {card.agent_id} - {card}, {type(card.skills)}")
        result += f"\n- {card.name}: {card.description}\n"
        if card.skills:
            if isinstance(card.skills[0], str):
                # 如果 skills 是字符串列表
                result += f"  技能: {', '.join(card.skills)}\n"
            else:
                # 如果 skills 是对象列表（有 name 属性）
                result += f"  技能: {', '.join([s.name for s in card.skills])}\n"
        else:
            result += "  技能: 无\n"
    return result