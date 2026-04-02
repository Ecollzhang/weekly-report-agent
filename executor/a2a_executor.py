import asyncio
import traceback
import uuid
import httpx
from typing import Dict, Any, Optional, List, Union
from types import SimpleNamespace

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    InternalError,
    InvalidParamsError,
    Part,
    Message,
    Task,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import new_agent_text_message
from a2a.utils.errors import ServerError

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import InMemorySaver

from memory.memory import AgentMemory
from agents.agent_card import registry, AgentCard, AgentCardPydantic


from utils.globalLogger import get_logger
logger = get_logger(__name__)

current_agent = {
    "name": "chat-agent"
}

class MultiAgentExecutor(AgentExecutor):
    """
    A2A Executor - 支持两种模式：
    1. 本地模式：直接路由到本地 agents（原有功能）
    2. A2A 模式：通过 A2A 协议调用远程 agents
    """
    
    def __init__(
        self,
        agents: Dict[str, Any] = None,  # 本地 agents
        memory: AgentMemory = None,
        default_agent: str = "chat",
        ui=None,
        enable_a2a: bool = False,  # 是否启用 A2A 远程调用
    ):
        self.agents = agents or {}  # 本地 agents
        self.memory = memory
        self.default_agent = default_agent
        self.ui = ui
        self.enable_a2a = enable_a2a
        self.conversation_states: Dict[str, Dict[str, Any]] = {}
        
        # A2A 相关
        self.http_client = None
        self.remote_agents: Dict[str, AgentCard] = {}  # 发现的远程 agents
        
        if enable_a2a:
            self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def discover_remote_agents(self, agent_urls: List[str]) -> None:
        """通过 A2A 发现机制获取远程智能体"""
        if not self.enable_a2a:
            return
        
        for url in agent_urls:
            try:
                # 标准 A2A 发现端点
                response = await self.http_client.get(f"{url}/.well-known/agent.json")
                if response.status_code == 200:
                    card_data = response.json()
                    card = AgentCard(
                        name=card_data.get("name", "Unknown"),
                        description=card_data.get("description", ""),
                        url=url,
                        version=card_data.get("version", "1.0.0"),
                        agent_id=card_data.get("agent_id", url),
                        skills=[s.get("name") for s in card_data.get("skills", [])]
                    )
                    self.remote_agents[card.agent_id] = card
                    logger.info(f"Discovered remote agent: {card.name} at {url}")
                    if self.ui:
                        self.ui.display_status("discovery", f"Found agent: {card.name}")
            except Exception as e:
                logger.warning(f"Failed to discover agent at {url}: {e}")
    
    async def _call_remote_agent(
        self, 
        agent_id: str, 
        message: str, 
        context_id: str, 
        task_id: str
    ) -> Optional[str]:
        """通过 A2A 协议调用远程智能体"""
        if not self.enable_a2a or not self.http_client:
            return None
        
        card = self.remote_agents.get(agent_id)
        if not card:
            logger.warning(f"Remote agent {agent_id} not found")
            return None
        
        try:
            # 构建 A2A 标准消息
            a2a_message = {
                "messageId": str(uuid.uuid4()),
                "parts": [{"root": {"text": message, "type": "text"}}],
                "role": "user"
            }
            
            response = await self.http_client.post(
                f"{card.url}/a2a/message",
                json={
                    "message": a2a_message,
                    "context_id": context_id,
                    "task_id": task_id
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                # 提取响应文本
                for artifact in result.get("artifacts", []):
                    for part in artifact.get("parts", []):
                        if part.get("root", {}).get("text"):
                            return part["root"]["text"]
                return result.get("response", "No response")
            else:
                return f"Error calling remote agent: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Remote agent call failed: {e}")
            return f"Error: {str(e)}"
    
    async def _route_with_a2a(self, message: str) -> Optional[str]:
        """使用 A2A 发现机制路由到远程智能体"""
        if not self.enable_a2a or not self.remote_agents:
            return None
        
        message_lower = message.lower()
        
        # 根据技能匹配远程智能体
        for agent_id, card in self.remote_agents.items():
            for skill in card.skills:
                if skill and skill.lower() in message_lower:
                    return agent_id
        
        return None
    
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> Optional[Union[Task, str]]:
        """Execute the agent request."""
        try:
            # Validate request
            if self._validate_request(context):
                raise ServerError(error=InvalidParamsError())
            
            # Extract message
            message = self._extract_message(context)
            if not message:
                raise ServerError(error=InvalidParamsError(message="No text content found"))
            
            context_id = context.context_id
            task_id = context.task_id
            
            # Create task updater if event_queue provided
            if event_queue:
                updater = TaskUpdater(event_queue, task_id, context_id)
                updater.submit()
                updater.update_status(
                    TaskState.working,
                    new_agent_text_message("Processing...", context_id, task_id),
                )
            else:
                updater = None
            
            response_text = None
            
            # ========== 1. 优先尝试 A2A 远程调用 ==========
            if self.enable_a2a:
                remote_agent_id = await self._route_with_a2a(message)
                if remote_agent_id:
                    if self.ui:
                        self.ui.display_status("a2a", f"Calling remote agent: {remote_agent_id}")
                    
                    response_text = await self._call_remote_agent(
                        remote_agent_id, message, context_id, task_id
                    )
                    # print(f"Received response from remote agent {remote_agent_id}: {response_text}")
                    if response_text and not response_text.startswith("Error"):
                        # 保存到记忆
                        self.memory.add_message(context_id, HumanMessage(content=message))
                        self.memory.add_message(context_id, AIMessage(content=response_text))
                        
                        if updater:
                            updater.add_artifact(
                                [Part(root=TextPart(text=response_text))],
                                name='agent_response',
                                metadata={"agent": remote_agent_id, "type": "remote"}
                            )
                            updater.complete()
                        
                        return self._format_response(response_text, task_id, context_id, event_queue)
            
            # ========== 2. 降级到本地路由 ==========
            agent_name = self._route_to_agent(message)
            agent = self.agents.get(agent_name, self.agents.get(self.default_agent))
            
            if not agent:
                raise ServerError(error=InternalError(message=f"Agent {agent_name} not found"))
            
            if self.ui:
                model_name = getattr(agent, 'model_name', 'unknown')
                self.ui.display_agent_routing(agent_name, model_name)
                self.ui.display_thinking()
            
            # Get conversation history
            history = self.memory.get_conversation_history(context_id) if self.memory else []
            
            # Prepare messages
            messages = history + [HumanMessage(content=message)]
            
            # Execute local agent
            try:
                config = {"configurable": {"thread_id": context_id}}
                if self.ui and hasattr(agent, 'callbacks'):
                    config["callbacks"] = agent.callbacks
                
                result = await agent.ainvoke(
                    {"messages": messages},
                    config=config
                )
                
                # Extract response
                if "messages" in result and result["messages"]:
                    last_message = result["messages"][-1]
                    response_text = last_message.content if hasattr(last_message, 'content') else str(last_message)
                elif "output" in result:
                    response_text = result["output"]
                else:
                    response_text = str(result)
                
                # Save to memory
                if self.memory:
                    self.memory.add_message(context_id, HumanMessage(content=message))
                    self.memory.add_message(context_id, AIMessage(content=response_text))
                
                # Update task if needed
                if updater:
                    updater.add_artifact(
                        [Part(root=TextPart(text=response_text))],
                        name='agent_response',
                        metadata={"agent": agent_name, "type": "local"}
                    )
                    updater.complete()
                
                return self._format_response(response_text, task_id, context_id, event_queue)
                    
            except Exception as e:
                logger.error(f"Local agent execution failed: {e}")
                logger.error(traceback.format_exc())
                if updater:
                    updater.failed(f"Agent execution failed: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Error in execute: {e}")
            logger.error(traceback.format_exc())
            raise ServerError(
                error=InternalError(
                    message=f"Execution error: {str(e)}"
                )
            )
    
    def _format_response(self, response_text: str, task_id: str, context_id: str, event_queue: EventQueue) -> Optional[Union[Task, str]]:
        """格式化响应"""
        if event_queue:
            return Task(
                id=task_id,
                context_id=context_id,
                status=TaskState.completed,
                artifacts=[{
                    "parts": [Part(root=TextPart(text=response_text))],
                    "name": "agent_response"
                }]
            )
        else:
            return response_text
    
    async def execute_with_message(self, message: Message, context_id: str, task_id: str) -> Optional[Union[Task, str]]:
        """Execute with direct message instead of RequestContext."""
        context = SimpleNamespace(
            message=message,
            context_id=context_id,
            task_id=task_id,
            configuration=None
        )
        return await self.execute(context, None)
    
    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        """Cancel the current task."""
        raise ServerError(error=UnsupportedOperationError())
    
    def _validate_request(self, context: RequestContext) -> bool:
        """Validate the request."""
        if not context.message or not context.message.parts:
            return True
        return False
    
    def _extract_message(self, context: RequestContext) -> Optional[str]:
        """Extract text from the request message."""
        text_parts = []
        
        if not context.message or not context.message.parts:
            return None
        
        for part in context.message.parts:
            part_content = part.root if hasattr(part, 'root') else part
            if isinstance(part_content, TextPart):
                text_parts.append(part_content.text)
        
        return '\n'.join(text_parts) if text_parts else None
    
    def _route_to_agent(self, message: str) -> str:
        """Route message to appropriate local agent based on content."""
        
        if current_agent["name"] in self.agents:
            return current_agent["name"]
        
        message_lower = message.lower()
        
        # Report generation
        if any(keyword in message_lower for keyword in [
            'report', 'generate report', 'create report', 'summary', 'analyze',
            'summarize', 'document'
        ]):
            return 'report-agent'
        
        # Git operations
        if any(keyword in message_lower for keyword in [
            'git', 'commit', 'push', 'pull', 'clone', 'repository', 'branch',
            'status', 'log', 'diff', 'merge'
        ]):
            return 'git-agent'
        
        
        # Default to chat agent
        return 'chat-agent'
    
    async def close(self):
        """关闭 HTTP 客户端"""
        if self.http_client:
            await self.http_client.aclose()