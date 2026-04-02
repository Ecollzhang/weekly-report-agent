import logging
from typing import List, Optional, Dict, Any
from langchain_core.tools import BaseTool

from utils.globalLogger import get_logger
logger = get_logger(__name__)


class MCPToolRegistry:
    """Registry for MCP (Model Context Protocol) tools."""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.mcp_servers: Dict[str, Any] = {}
    
    async def register_tool(self, name: str, tool: BaseTool) -> None:
        """Register a tool with the registry."""
        self.tools[name] = tool
        logger.info(f"Registered tool: {name}")
    
    async def register_mcp_server(self, server_name: str, server_config: Dict[str, Any]) -> None:
        """Register an MCP server and load its tools."""
        try:
            # Placeholder for MCP server integration
            # In production, you would use langchain-mcp-adapters to connect to MCP servers
            logger.info(f"Registered MCP server: {server_name}")
            self.mcp_servers[server_name] = server_config
            
            # Example: Load tools from MCP server
            # from langchain_mcp_adapters import load_mcp_tools
            # tools = await load_mcp_tools(server_config)
            # for tool in tools:
            #     await self.register_tool(tool.name, tool)
            
        except Exception as e:
            logger.error(f"Failed to register MCP server {server_name}: {e}")
    
    async def get_tools(self) -> List[BaseTool]:
        """Get all registered tools."""
        return list(self.tools.values())
    
    async def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a specific tool by name."""
        return self.tools.get(name)
    
    async def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self.tools.keys())