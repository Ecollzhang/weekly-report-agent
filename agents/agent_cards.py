# agent_cards.py
import logging
from .agent_card import AgentCard, registry

from utils.globalLogger import get_logger
logger = get_logger(__name__)


# ============ 定义各个智能体的 Agent Card ============

# Chat Agent Card
chat_card = AgentCard(
    name="Chat Assistant",
    description="Main conversation agent that coordinates with other specialized agents",
    url="http://localhost:8001/a2a",
    version="1.0.0",
    agent_id="chat-agent",
    skills=["general_chat", "coordination", "question_answering"]
)

# Git Agent Card
git_card = AgentCard(
    name="Git Operations Agent",
    description="Specialized agent for Git operations and version control",
    url="http://localhost:8002/a2a",
    version="1.0.0",
    agent_id="git-agent",
    skills=["git_status", "git_log", "git_diff", "git_branch", "git_show"]
)

# Report Agent Card
report_card = AgentCard(
    name="Report Generation Agent",
    description="Specialized agent for generating reports and summaries",
    url="http://localhost:8003/a2a",
    version="1.0.0",
    agent_id="report-agent",
    skills=["generate_report", "summarize", "extract_key_points", 'get_report_template', 'report']
)


def register_all_agents(agent_instances: dict = None):
    """注册所有智能体到注册表"""
    registry.register("chat-agent", chat_card, agent_instances.get("chat") if agent_instances else None)
    registry.register("git-agent", git_card, agent_instances.get("git") if agent_instances else None)
    registry.register("report-agent", report_card, agent_instances.get("report") if agent_instances else None)
    logger.info("All agents registered in A2A registry")


def get_agent_card_for_server(agent_id: str) -> dict:
    """获取用于 A2A 服务器响应的 Agent Card（Pydantic 格式）"""
    card = registry.get_card(agent_id)
    if card:
        return card.to_pydantic().to_dict()
    return None