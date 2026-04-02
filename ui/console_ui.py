import os
from typing import Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.table import Table
from rich import box
from rich.layout import Layout
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn
import time

class ConsoleUI:
    """Console UI for multi-agent system."""
    
    def __init__(self):
        self.console = Console()
        self.current_spinner = None
    
    def get_input(self) -> str:
        """Get user input with prompt."""
        self.console.print("\n[bold green]You:[/bold green] ", end="")
        return input()
    
    def display_response(self, response: Any) -> None:
        """Display agent response."""
        self.console.print("\n[bold cyan]Agent:[/bold cyan]")
        
        if isinstance(response, str):
            self.console.print(Panel(
                Markdown(response),
                title="Response",
                border_style="cyan"
            ))
        elif hasattr(response, 'status'):
            if response.status == "completed":
                if hasattr(response, 'artifacts') and response.artifacts:
                    for artifact in response.artifacts:
                        if artifact.get('parts'):
                            for part in artifact['parts']:
                                if hasattr(part.root, 'text'):
                                    self.console.print(Panel(
                                        Markdown(part.root.text),
                                        title="Response",
                                        border_style="green"
                                    ))
                else:
                    self.console.print(Panel(
                        Markdown("Task completed successfully."),
                        title="Status",
                        border_style="green"
                    ))
            else:
                self.console.print(Panel(
                    Text(f"Task status: {response.status}", style="yellow"),
                    title="Status",
                    border_style="yellow"
                ))
        else:
            self.console.print(Panel(
                Markdown(str(response)),
                title="Response",
                border_style="yellow"
            ))
    
    def display_error(self, error: str) -> None:
        """Display error message."""
        self.console.print(Panel(
            Text(error, style="red"),
            title="Error",
            border_style="red"
        ))
    
    def show_help(self, agents: Dict[str, Any]) -> None:
        """Show help information."""
        table = Table(title="Available Commands", box=box.ROUNDED)
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("Description", style="green")
        
        table.add_row("help", "Show this help message")
        table.add_row("clear", "Clear the screen")
        table.add_row("exit/quit", "Exit the application")
        table.add_row("", "")
        table.add_row("[any text]", "Send message to the agent system")
        
        self.console.print(table)
        
        # Show available agents
        if agents:
            agent_table = Table(title="Available Agents", box=box.SIMPLE)
            agent_table.add_column("Agent", style="cyan")
            agent_table.add_column("Description", style="green")
            
            for name, agent in agents.items():
                desc = getattr(agent, 'description', 'No description')
                agent_table.add_row(name, desc)
            
            self.console.print("\n")
            self.console.print(agent_table)
            
            # Show example queries
            example_table = Table(title="Example Queries", box=box.SIMPLE)
            example_table.add_column("Query Type", style="cyan")
            example_table.add_column("Example", style="green")
            
            example_table.add_row("Chat", "What's the weather like?")
            example_table.add_row("Git", "Show me the git status")
            example_table.add_row("Report", "Generate a report about the project")
            
            self.console.print("\n")
            self.console.print(example_table)
    
    def clear_screen(self) -> None:
        """Clear the console screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_status(self, status: str, message: str = "") -> None:
        """Display status message."""
        self.console.print(f"[dim]{status}: {message}[/dim]")
    
    def display_model_info(self, model_name: str):
        """显示正在使用的模型"""
        self.console.print(f"[dim]🤖 Using model: [cyan]{model_name}[/cyan][/dim]")
    
    def display_tool_call(self, tool_name: str, input_str: str):
        """显示工具调用（不显示输出）"""
        # 截断过长的输入
        if len(input_str) > 50:
            input_str = input_str[:47] + "..."
        
        self.console.print(f"[yellow]🔧 Calling tool: [bold]{tool_name}[/bold] with input: {input_str}[/yellow]")
    
    def display_agent_routing(self, agent_name: str, model_name: str = None):
        """显示路由信息和模型"""
        if model_name:
            self.console.print(f"[dim]🎯 Routing to [cyan]{agent_name}[/cyan] agent (model: {model_name})...[/dim]")
        else:
            self.console.print(f"[dim]🎯 Routing to [cyan]{agent_name}[/cyan] agent...[/dim]")
    
    def display_thinking(self):
        """显示正在思考"""
        self.console.print("[dim]💭 Thinking...[/dim]")
    
    def display_response_start(self):
        """开始显示响应"""
        self.console.print("[bold cyan]🤖 Agent:[/bold cyan]")