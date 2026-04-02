# agent_card.py
import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from dataclasses import dataclass, asdict

from utils.globalLogger import get_logger
logger = get_logger(__name__)


# ============ Pydantic 版本（用于 API 序列化）============
class Skill(BaseModel):
    """智能体技能"""
    id: str
    name: str
    description: str
    inputModes: List[str] = Field(default=["text"])
    outputModes: List[str] = Field(default=["text"])
    examples: Optional[List[str]] = None


class Authentication(BaseModel):
    """认证配置"""
    schemes: List[str] = Field(default=["Bearer"])
    url: Optional[str] = None
    description: Optional[str] = None


class AgentCardPydantic(BaseModel):
    """Agent Card - Pydantic 版本，用于 API 序列化"""
    name: str
    description: str
    provider: str
    url: str
    version: str = Field(default="1.0.0")
    agent_id: Optional[str] = None
    capabilities: List[str] = Field(default=["streaming"])
    authentication: Optional[Authentication] = None
    skills: List[Skill] = Field(default=[])
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentCardPydantic":
        return cls(**data)


# ============ Dataclass 版本（用于内部使用）============
@dataclass
class AgentCard:
    """Agent Card - Dataclass 版本，用于内部使用"""
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    agent_id: str = ""
    skills: List[str] = None  # 简单版本，只存技能名称列表
    
    def __post_init__(self):
        if self.skills is None:
            self.skills = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_pydantic(self, provider: str = "Local AI") -> AgentCardPydantic:
        """转换为 Pydantic 版本用于 API"""
        return AgentCardPydantic(
            name=self.name,
            description=self.description,
            provider=provider,
            url=self.url,
            version=self.version,
            agent_id=self.agent_id,
            skills=[
                Skill(
                    id=skill,
                    name=skill,
                    description=f"{skill} operation",
                    inputModes=["text"],
                    outputModes=["text"]
                )
                for skill in self.skills
            ]
        )


# ============ 注册表 ============
class AgentRegistry:
    """智能体注册表"""
    
    def __init__(self):
        self._agents: Dict[str, AgentCard] = {}
        self._agent_instances: Dict[str, Any] = {}
    
    def register(self, agent_id: str, card: AgentCard, instance: Any = None) -> None:
        """注册智能体"""
        card.agent_id = agent_id
        self._agents[agent_id] = card
        if instance:
            self._agent_instances[agent_id] = instance
        logger.info(f"Registered agent: {agent_id} - {card.name}")
    
    def get_card(self, agent_id: str) -> Optional[AgentCard]:
        return self._agents.get(agent_id)
    
    def get_instance(self, agent_id: str) -> Optional[Any]:
        return self._agent_instances.get(agent_id)
    
    def list_agents(self) -> List[AgentCard]:
        return list(self._agents.values())
    
    def discover_by_skill(self, skill: str) -> List[AgentCard]:
        """根据技能发现智能体"""
        return [card for card in self._agents.values() if skill in card.skills]
    
    def to_pydantic_cards(self, provider: str = "Local AI") -> List[Dict]:
        """返回所有 Agent Card 的 Pydantic 版本（用于 API）"""
        return [card.to_pydantic(provider).to_dict() for card in self._agents.values()]


# 全局注册表实例
registry = AgentRegistry()