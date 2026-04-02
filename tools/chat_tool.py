from typing import Optional

from langchain_core.tools import tool
import logging
from langchain_core.tools import tool
from datetime import datetime
import pytz  # 如果需要时区支持

from utils.globalLogger import get_logger
logger = get_logger(__name__)

@tool
def get_current_task() -> str:
    """Get the current task or context for the agent."""
    # 这里可以根据实际情况返回当前任务或上下文信息
    with open("workspace/task.md", "r", encoding="utf-8") as f:
        task = f.read().strip()
    if task:
        return f"当前任务: {task}"
    return "当前没有特定任务，等待用户输入指令。"

@tool
def get_current_date(timezone: Optional[str] = None) -> str:
    """Get the current date and time.
    
    Args:
        timezone: Optional timezone (e.g., "Asia/Shanghai", "America/New_York")
                  If not provided, returns local time.
    
    Returns:
        Current date and time in a readable format
    """
    try:
        if timezone:
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)
        else:
            now = datetime.now()
        
        # 返回多种格式
        return {
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "weekday": now.strftime("%A"),
            "timezone": timezone or "local"
        }
    except Exception as e:
        return f"Error getting date: {str(e)}"

@tool
def write_to_file(filename: str, content: str) -> str:
    """Write content to a file."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Content successfully written to {filename}"
    except Exception as e:
        return f"Error writing to file: {str(e)}"

@tool
def read_from_file(filename: str) -> str:
    """Read content from a file."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading from file: {str(e)}"

@tool
def echo_tool(message: str) -> str:
    """Simple echo tool for testing."""
    return f"Echo: {message}"


@tool
def calculate(expression: str) -> str:
    """Calculate mathematical expressions."""
    try:
        # Safe evaluation of mathematical expressions
        allowed_names = {
            k: v for k, v in __import__('math').__dict__.items() 
            if not k.startswith("__")
        }
        allowed_names.update({
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "len": len, "int": int, "float": float
        })
        
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"Result: {result}"
    except Exception as e:
        return f"Error calculating: {str(e)}"