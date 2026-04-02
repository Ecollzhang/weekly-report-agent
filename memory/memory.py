import json
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from utils.globalLogger import get_logger
logger = get_logger(__name__)


class AgentMemory:
    """Memory management for multi-agent conversations."""
    
    def __init__(self, max_history: int = 100, persist_path: str = "workspace/agent_memory.json"):
        self.conversations: Dict[str, List[BaseMessage]] = defaultdict(list)
        self.max_history = max_history
        self.metadata: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        self.persist_path = persist_path
        
        # 加载已保存的记忆
        self._load_from_file()
    
    # ============ 消息序列化/反序列化 ============
    
    def _serialize_message(self, message: BaseMessage) -> Dict[str, Any]:
        """将 LangChain 消息序列化为 JSON 可存储的格式"""
        message_type = "human" if isinstance(message, HumanMessage) else "ai" if isinstance(message, AIMessage) else "system"
        
        return {
            "type": message_type,
            "content": message.content,
            "additional_kwargs": message.additional_kwargs,
            "timestamp": datetime.now().isoformat()
        }
    
    def _deserialize_message(self, data: Dict[str, Any]) -> BaseMessage:
        """从 JSON 数据反序列化消息"""
        msg_type = data.get("type")
        content = data.get("content", "")
        additional_kwargs = data.get("additional_kwargs", {})
        
        if msg_type == "human":
            return HumanMessage(content=content, additional_kwargs=additional_kwargs)
        elif msg_type == "ai":
            return AIMessage(content=content, additional_kwargs=additional_kwargs)
        else:
            return SystemMessage(content=content, additional_kwargs=additional_kwargs)
    
    # ============ 持久化操作 ============
    
    def _save_to_file(self) -> None:
        """保存所有记忆到 JSON 文件"""
        try:
            data = {
                "conversations": {},
                "metadata": dict(self.metadata),
                "saved_at": datetime.now().isoformat()
            }
            
            # 序列化会话历史
            for session_id, messages in self.conversations.items():
                data["conversations"][session_id] = [
                    self._serialize_message(msg) for msg in messages
                ]
            
            # 写入文件（原子操作）
            temp_file = f"{self.persist_path}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 重命名实现原子写入
            os.replace(temp_file, self.persist_path)
            
            logger.debug(f"Memory saved to {self.persist_path}, {len(self.conversations)} sessions")
            
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
    
    def _load_from_file(self) -> None:
        """从 JSON 文件加载记忆"""
        if not os.path.exists(self.persist_path):
            logger.info(f"No existing memory file found at {self.persist_path}, starting fresh")
            return
        
        try:
            with open(self.persist_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 加载会话历史
            for session_id, messages_data in data.get("conversations", {}).items():
                self.conversations[session_id] = [
                    self._deserialize_message(msg_data) for msg_data in messages_data
                ]
            
            # 加载元数据
            self.metadata.update(data.get("metadata", {}))
            
            logger.info(f"Loaded memory from {self.persist_path}, {len(self.conversations)} sessions")
            
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")
    

    def add_message(
        self, 
        session_id: str, 
        message: BaseMessage,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a message to conversation history."""
        conversation = self.conversations[session_id]
        conversation.append(message)
        
        # Trim if exceeds max history
        if len(conversation) > self.max_history:
            self.conversations[session_id] = conversation[-self.max_history:]
        
        # Update metadata
        if metadata:
            self.metadata[session_id].update(metadata)
        self._save_to_file()  # 每次添加消息后保存到文件
        logger.debug(f"Added message to session {session_id}, total: {len(conversation)}")
    
    def get_conversation_history(
        self, 
        session_id: str, 
        limit: Optional[int] = None
    ) -> List[BaseMessage]:
        """Get conversation history for a session."""
        conversation = self.conversations.get(session_id, [])
        
        if limit:
            return conversation[-limit:]
        return conversation
    
    def clear_session(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        if session_id in self.conversations:
            self.conversations[session_id] = []
            self.metadata[session_id] = {}
            logger.info(f"Cleared session {session_id}")
    
    def get_metadata(self, session_id: str) -> Dict[str, Any]:
        """Get metadata for a session."""
        return self.metadata.get(session_id, {})
    
    def set_metadata(self, session_id: str, key: str, value: Any) -> None:
        """Set metadata for a session."""
        self.metadata[session_id][key] = value
    
    def get_summary(self, session_id: str) -> str:
        """Get a summary of the conversation."""
        conversation = self.conversations.get(session_id, [])
        
        if not conversation:
            return "No conversation history"
        
        summary = f"Conversation has {len(conversation)} messages:\n\n"
        
        for i, msg in enumerate(conversation[-10:], 1):  # Show last 10
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            summary += f"{i}. {role}: {content}\n"
        
        return summary