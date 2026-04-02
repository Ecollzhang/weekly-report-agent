from langchain_core.callbacks import BaseCallbackHandler

class ToolCallCallback(BaseCallbackHandler):
    def __init__(self, ui):
        self.ui = ui
        
    def on_tool_start(self, serialized, input_str, **kwargs):
        """当工具开始执行时调用"""
        tool_name = serialized.get("name", "unknown")
        self.ui.display_tool_call(tool_name, input_str)
        
    def on_tool_end(self, output, **kwargs):
        """当工具执行完成时调用"""
        pass  # 不显示工具输出

