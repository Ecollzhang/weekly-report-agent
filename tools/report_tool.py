from typing import Dict, List, Optional

from langchain_core.tools import tool
@tool
def get_report_template() -> str:
    """获取周报模板内容。如果模板文件存在则返回文件内容，否则返回默认模板。"""
    try:
        with open("/workspace/report_template.md", "r", encoding="utf-8") as f:
            template = f.read()
        return template
    except Exception as e:
        template = """
        获取周报模板失败，使用默认模板
        周报模板:
        
        1. 本周工作内容
        - 工作1: 描述工作内容和完成情况
        - 工作2: 描述工作内容和完成情况
        
        2. 下周工作计划
        - 计划1: 描述计划内容和目标
        - 计划2: 描述计划内容和目标
        
        3. 遇到的问题及解决方案
        - 问题1: 描述问题和解决方案
        - 问题2: 描述问题和解决方案
        
        4. 其他备注
        - 备注1: 其他需要说明的事项
        - 备注2: 其他需要说明的事项
        """
    return template


@tool
def write_report_to_file(report_content: str, filename: str = "weekly_report.md") -> str:
    """将生成的报告内容写入文件。
    
    Args:
        report_content: 要写入的报告内容
        filename: 保存的文件名，默认为 weekly_report.md
    
    Returns:
        操作结果信息
    """
    try:
        with open(f"workspace/{filename}", "w", encoding="utf-8") as f:
            f.write(report_content)
        return f"报告已保存到 workspace/{filename}"
    except Exception as e:
        return f"保存报告失败: {e}"