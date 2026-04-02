# a2a_server.py
import asyncio
import logging
import uuid
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from agents.agent_card import registry

from utils.globalLogger import get_logger
logger = get_logger(__name__)


# A2A 数据模型
class A2APart(BaseModel):
    root: Dict[str, Any]


class A2AMessage(BaseModel):
    messageId: str
    parts: list[A2APart]
    role: str = "user"


class A2ARequest(BaseModel):
    message: A2AMessage
    context_id: str
    task_id: str


class A2AArtifact(BaseModel):
    parts: list[A2APart]
    name: Optional[str] = None


class A2AResponse(BaseModel):
    task_id: str
    context_id: str
    status: str
    artifacts: list[A2AArtifact] = []
    error: Optional[str] = None


class AgentWrapper:
    """包装 LangGraph agent，使其支持 A2A 协议"""
    
    def __init__(self, agent, memory=None):
        self.agent = agent
        self.memory = memory
    
    async def handle_a2a_message(self, message: str, context: dict) -> str:
        """处理 A2A 消息"""
        context_id = context.get("context_id", "default")
        
        # 获取历史
        messages = []
        if self.memory:
            history = self.memory.get_conversation_history(context_id)
            messages = history
        
        # 添加当前消息
        from langchain_core.messages import HumanMessage
        messages.append(HumanMessage(content=message))
        
        # 调用 agent
        config = {"configurable": {"thread_id": context_id}}
        result = await self.agent.ainvoke({"messages": messages}, config=config)
        
        # 提取响应
        if "messages" in result and result["messages"]:
            last_msg = result["messages"][-1]
            response = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
        else:
            response = str(result)
        
        # 保存到记忆
        if self.memory:
            from langchain_core.messages import AIMessage
            self.memory.add_message(context_id, HumanMessage(content=message))
            self.memory.add_message(context_id, AIMessage(content=response))
        
        return response


class A2AServer:
    """A2A 协议服务器 - 让智能体可以被其他智能体调用"""
    
    def __init__(self, agent, agent_id: str, port: int, host: str = "localhost", memory=None):
        self.agent = agent
        self.agent_id = agent_id
        self.port = port
        self.host = host
        self.app = None
        self._server = None
        self.memory = memory

        if hasattr(agent, 'ainvoke') and not hasattr(agent, 'handle_a2a_message'):
            self.wrapped_agent = AgentWrapper(agent, memory)
        else:
            self.wrapped_agent = agent
        
        # print(f"Initializing A2A server for agent: {agent_id} on port {port}", registry.list_agents())
        # 从注册表获取 Agent Card
        self.card = registry.get_card(agent_id)
        if not self.card:
            raise ValueError(f"Agent {agent_id} not found in registry")
        
        # 更新 URL
        self.card.url = f"http://{host}:{port}"
        
        self._create_app()
    
    def _create_app(self):
        self.app = FastAPI(title=f"{self.card.name} - A2A Server")
        
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Agent Card 发现端点
        @self.app.get("/.well-known/agent.json")
        async def get_agent_card():
            return self.card.to_pydantic().to_dict()
        
        # A2A 消息端点
        @self.app.post("/a2a/message")
        async def handle_message(request: A2ARequest) -> A2AResponse:
            # 提取消息文本
            message_text = ""
            for part in request.message.parts:
                if part.root.get("text"):
                    message_text += part.root.get("text", "")
            
            if not message_text:
                raise HTTPException(status_code=400, detail="No text content")
            
            try:
                # 调用智能体处理
                response_text = await self.wrapped_agent.handle_a2a_message(
                    message_text,
                    {"context_id": request.context_id, "task_id": request.task_id}
                )
                logger.info(f"A2A message processed successfully for agent {self.agent_id}, {response_text}")
                return A2AResponse(
                    task_id=request.task_id,
                    context_id=request.context_id,
                    status="completed",
                    artifacts=[A2AArtifact(
                        parts=[A2APart(root={"text": response_text, "type": "text"})],
                        name="response"
                    )]
                )
            except Exception as e:
                logger.error(f"Error processing A2A message: {e}")
                return A2AResponse(
                    task_id=request.task_id,
                    context_id=request.context_id,
                    status="failed",
                    error=str(e)
                )
        
        @self.app.get("/health")
        async def health():
            return {"status": "healthy"}
    
    async def start(self):
        try:
            """启动服务器"""
            config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="warning")
            self._server = uvicorn.Server(config)
            asyncio.create_task(self._server.serve())
            await asyncio.sleep(0.5)
            logger.info(f"A2A server for {self.card.name} started at http://{self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to start A2A server: {e}")
            # raise
    
    async def stop(self):
        """停止服务器"""
        if self._server:
            self._server.should_exit = True
            await asyncio.sleep(0.5)