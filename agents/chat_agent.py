import logging
from typing import Optional, List, Any, Dict

from langchain.agents import create_agent

from langgraph.checkpoint.memory import InMemorySaver

from langchain_core.callbacks import BaseCallbackHandler
from rich.console import Console

from utils.toolCallCallback import ToolCallCallback  # 添加工具调用回调
from tools.chat_tool import echo_tool, calculate, get_current_date, get_current_task, write_to_file
from tools.a2a_client import call_git_agent, call_report_agent, get_available_agents, get_agent_skills

from llm.llm_factory import get_llm

from tools.mcp_registry import MCPToolRegistry
from memory.memory import AgentMemory

from utils.globalLogger import get_logger
logger = get_logger(__name__)

console = Console()

class ToolCallCallback(BaseCallbackHandler):
    def __init__(self, ui):
        self.ui = ui
        
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs):
        """当工具开始执行时调用"""
        tool_name = serialized.get("name", "unknown")
        self.ui.display_tool_call(tool_name, input_str)
        
    def on_tool_end(self, output: str, **kwargs):
        """当工具执行完成时调用"""
        # 不显示工具输出，只显示完成状态
        pass


async def create_chat_agent(
    name: str = "ChatAgent",
    description: str = "General conversation agent",
    memory: Optional[AgentMemory] = None,
    tools: Optional[List] = None,
    ui=None,  # 添加 UI 参数
) -> Any:
    """Create a general chat agent with LangChain."""
    
    # Initialize LLM
    model_name, llm = get_llm()
    
    # Load MCP tools
    if tools is None:
        mcp_registry = MCPToolRegistry()
        tools = await mcp_registry.get_tools()
    
    # Add default tools
    default_tools = [echo_tool, calculate, get_current_task, write_to_file]
    a2a_tools = [get_available_agents, get_agent_skills, call_git_agent, call_report_agent]

    all_tools = tools + default_tools + a2a_tools

    
    # 创建回调
    callbacks = [ToolCallCallback(ui)] if ui else []
    
    # Create memory saver
    checkpointer = InMemorySaver()
    
    # Create agent
    agent = create_agent(
            model=llm,
            tools=all_tools,
            system_prompt=f"""You are {name}, a helpful AI assistant that can coordinate with specialized agents.

    {description}

    ## Your Capabilities
    - Have natural conversations
    - call 'get_current_task()' to get your current task if user ask to start a task
    - Use available tools to help with tasks
    - get avaliable agents and their skills using 'get_available_agents()' and 'get_agent_skills(agent_id)'
    - **Call other agents** when specialized help is needed

    ## Available Agents You Can Call
    - **Git Agent**: Use `call_git_agent()` for Git operations (status, log, branch, diff)
    - **Report Agent**: Use `call_report_agent()` for generating reports and summaries
    - Use `get_available_agents()` to see all available agents

    ## When to Call Other Agents
    - If user asks about Git/repository: call Git Agent
    - If user wants a report or summary: call Report Agent  
    - For general conversation: respond directly

    ## Important Rules
    1. When calling another agent, explain what you're doing to the user
    2. Always use the appropriate tool for the task
    3. If the user's request involves Git, you MUST call Git Agent
    4. If the user wants a report or summary, you MUST call Report Agent
    5. Combine information from multiple agents if needed

    Be helpful, friendly, and accurate.""",
            checkpointer=checkpointer,
        )
        
    # 存储模型名称和回调供外部使用
    agent.model_name = model_name
    agent.callbacks = callbacks
    
    logger.info(f"Created chat agent: {name} with model {model_name}")
    return agent