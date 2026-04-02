import asyncio
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from a2a.server.agent_execution import RequestContext
from a2a.types import Message, TextPart, Part, Task, TaskState
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import uuid

from executor.a2a_executor import MultiAgentExecutor, current_agent
from agents.chat_agent import create_chat_agent
from agents.git_agent import create_git_agent
from agents.report_agent import create_report_agent
from memory.memory import AgentMemory
from ui.console_ui import ConsoleUI

from agents.agent_card import registry as agent_registry
from agents.agent_cards import register_all_agents
from server.a2a_server import A2AServer  
from utils.globalLogger import get_logger, global_logger
global_logger.set_log_dir("logs")

# Load environment variables
load_dotenv()

logger = get_logger(__name__)
console = Console()


class MultiAgentA2ASystem:
    """Main system orchestrating multiple agents with A2A protocol."""
    
    def __init__(self):
        self.agents = {}
        self.executor: Optional[MultiAgentExecutor] = None
        self.memory: Optional[AgentMemory] = None
        self.ui = ConsoleUI()
        self.a2a_servers = []
        
    async def initialize(self):
        """Initialize all agents and components."""
        console.print(Panel.fit(
            "[bold cyan]🤖 Multi-Agent A2A System Initializing[/bold cyan]",
            border_style="cyan"
        ))
        
        # Initialize memory
        self.memory = AgentMemory()
        
        # Initialize agents
        console.print("[yellow]Creating agents...[/yellow]")
        
        console.print("  - Chat Agent...")
        self.agents['chat-agent'] = await create_chat_agent(
            name="ChatAgent",
            description="General conversation agent for answering questions and having natural dialogues",
            memory=self.memory,
            ui=self.ui
        )
        
        console.print("  - Git Agent...")
        self.agents['git-agent'] = await create_git_agent(
            name="GitAgent", 
            description="Git operations agent for repository management and version control",
            memory=self.memory,
            ui=self.ui
        )
        
        console.print("  - Report Agent...")
        self.agents['report-agent'] = await create_report_agent(
            name="ReportAgent",
            description="Report generation agent for creating structured documents and summaries",
            memory=self.memory,
            ui=self.ui
        )

        # 注册到 A2A 注册表
        register_all_agents(self.agents)

        # 为每个智能体启动 A2A 服务器
        ports = {"git-agent": 8002, "report-agent": 8003}
        for agent_name, agent in self.agents.items():
            if agent_name in ports:
                server = A2AServer(
                    agent=agent,
                    agent_id=agent_name,
                    port=ports[agent_name],
                    host="localhost"
                )
                await server.start()
                self.a2a_servers.append(server)
        
        # 显示可用智能体
        console.print("[green]✓ A2A agents registered:[/green]")
        for card in agent_registry.list_agents():
            console.print(f"  - {card.name} ({card.agent_id})")
        
        # ========== 修改点 1: 初始化 executor 时启用 A2A ==========
        self.executor = MultiAgentExecutor(
            agents=self.agents,
            memory=self.memory,
            default_agent="chat",
            ui=self.ui,
            enable_a2a=True  # 启用 A2A 远程调用
        )
        
        # ========== 修改点 2: 发现远程智能体（如果需要调用外部服务）==========
        # 如果有其他远程 A2A 服务，可以在这里发现
        # 例如：await self.executor.discover_remote_agents([
        #     "http://localhost:8002",
        #     "http://localhost:8003",
        # ])
        
        console.print("[green]✓ All agents initialized successfully![/green]\n")
        
    async def run_interactive(self):
        """Run interactive console session."""
        console.print(Panel(
            "Welcome to Multi-Agent A2A System!\n"
            "Type 'help' for available commands, 'exit' to quit.\n\n"
            "The system will automatically route your request to the appropriate agent:\n"
            "  • Chat Agent - General conversations\n"
            "  • Git Agent - Git operations and version control\n"
            "  • Report Agent - Report generation and summarization",
            title="Welcome",
            border_style="green"
        ))
        
        context_id = "default_session"
        task_counter = 1
        
        while True:
            try:
                user_input = self.ui.get_input()
                
                if user_input.lower() in ['exit', 'quit']:
                    console.print("\n[bold red]Goodbye![/bold red]")
                    break
                    
                if user_input.lower() == 'help':
                    self.ui.show_help(self.agents)
                    continue
                    
                if user_input.lower() == 'clear':
                    self.ui.clear_screen()
                    continue
                
                if user_input.lower().startswith('@'):
                    current_agent["name"] = user_input[1:].strip()
                    logger.info(f"Switching current agent to: {current_agent['name']}")
                    continue

                if not user_input.strip():
                    continue
                
                task_id = f"task_{task_counter}"
                await self.process_message(user_input, context_id, task_id)
                task_counter += 1
                
            except KeyboardInterrupt:
                console.print("\n\n[bold red]Interrupted. Goodbye![/bold red]")
                break
            except Exception as e:
                console.print(f"[bold red]Error: {e}[/bold red]")
                logger.exception("Error in interactive session")
        
        for server in self.a2a_servers:
            await server.stop()
    
    async def process_message(self, message: str, context_id: str, task_id: str):
        """Process a single message through the agent system."""
        a2a_message = Message(
            messageId=str(uuid.uuid4()),
            parts=[Part(root=TextPart(text=message))],
            role="user"
        )
        
        try:
            # ========== 修改点 3: 直接调用 execute_with_message ==========
            result = await self.executor.execute_with_message(a2a_message, context_id, task_id)
            if result:
                self.ui.display_response(result)
        except Exception as e:
            self.ui.display_error(str(e))
            raise
    
    # ========== 修改点 4: 添加清理方法 ==========
    async def cleanup(self):
        """清理资源"""
        if self.executor:
            await self.executor.close()


async def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if not os.getenv('DASHSCOPE_API_KEY') and not os.getenv('OPENAI_API_KEY'):
        console.print("[bold red]Error: Neither DASHSCOPE_API_KEY nor OPENAI_API_KEY found in environment variables![/bold red]")
        console.print("Please set one of them in your .env file")
        return
    
    system = MultiAgentA2ASystem()
    try:
        await system.initialize()
        await system.run_interactive()
    finally:
        await system.cleanup()


if __name__ == "__main__":
    asyncio.run(main())