import logging
from typing import Optional, Any, List, Dict
from datetime import datetime

from langchain.agents import create_agent

from langgraph.checkpoint.memory import InMemorySaver

from llm.llm_factory import get_llm
from memory.memory import AgentMemory
from utils.toolCallCallback import ToolCallCallback  # 添加工具调用回调
from tools.report_tool import get_report_template, write_report_to_file
from tools.chat_tool import read_from_file, write_to_file
from utils.globalLogger import get_logger
logger = get_logger(__name__)

async def create_report_agent(
    name: str = "ReportAgent",
    description: str = "Report generation agent",
    memory: Optional[AgentMemory] = None,
    ui=None,  # 添加 ui 参数
) -> Any:
    """Create a report generation agent."""
    
    model_name, llm = get_llm()
    
    report_tools = [get_report_template, write_report_to_file, read_from_file]
    
    callbacks = [ToolCallCallback(ui)] if ui else []
    
    checkpointer = InMemorySaver()
    
    agent = create_agent(
        model=llm,
        tools=report_tools,
        system_prompt=f"""You are {name}, a specialized report generation assistant.

{description}

You can help with:
- Creating structured reports from information
- Summarizing long documents
- Extracting key points from text
- Formatting reports with proper sections
- Adding metadata like dates and titles
- Organizing information logically

When generating reports:
1. Always start with a clear title
2. Organize content into logical sections
3. Use bullet points for lists
4. Include dates for reference
5. Highlight key findings

Always produce clear, well-structured, professional reports.""",
        checkpointer=checkpointer,
    )
    
    # 存储模型名称和回调供外部使用
    agent.model_name = model_name
    agent.callbacks = callbacks
    
    logger.info(f"Created report agent: {name} with model {model_name}")
    return agent