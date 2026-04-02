import logging
from typing import Optional, Any

from langchain.agents import create_agent

from langgraph.checkpoint.memory import InMemorySaver

from utils.toolCallCallback import ToolCallCallback  # 添加工具调用回调

from memory.memory import AgentMemory

from llm.llm_factory import get_llm

from tools.git_tool import git_status, git_log, git_diff, git_branch
from tools.chat_tool import get_current_date

from utils.globalLogger import get_logger
logger = get_logger(__name__)



async def create_git_agent(
    name: str = "GitAgent",
    description: str = "Git operations agent",
    memory: Optional[AgentMemory] = None,
    ui=None,  # 添加 ui 参数
) -> Any:
    """Create a Git operations agent."""
    
    model_name, llm = get_llm()
    
    # Git tools
    git_tools = [git_status, git_log, git_diff, git_branch, get_current_date]

    callbacks = [ToolCallCallback(ui)] if ui else []

    checkpointer = InMemorySaver()
    
    agent = create_agent(
        model=llm,
        tools=git_tools,
        system_prompt=f"""You are {name}, a specialized Git operations assistant.

{description}

You can help with:
- getting current date
- Checking repository status
- Viewing commit history
- Showing differences between commits/files
- Listing branches
- Explaining git concepts
- Suggesting git commands

Always be careful with git operations and explain what you're doing.
Never run destructive commands like force push without explicit confirmation.""",
        checkpointer=checkpointer,
    )
    
    # 存储模型名称和回调供外部使用
    agent.model_name = model_name
    agent.callbacks = callbacks
    
    logger.info(f"Created git agent: {name} with model {model_name}")
    return agent