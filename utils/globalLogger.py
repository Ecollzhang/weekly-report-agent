# logging_config.py
import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional


class GlobalLogger:
    """全局日志管理器"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.loggers = {}
        self.log_dir = "logs"
        self._setup_root_logger()
    
    def _setup_root_logger(self):
        """配置根日志器"""
        # 创建日志目录
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)
        
        # 获取根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # 移除现有处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 添加文件处理器（按日期轮转）
        file_handler = TimedRotatingFileHandler(
            filename=os.path.join(self.log_dir, "app.log"),
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志器"""
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(name)
        return self.loggers[name]
    
    def set_level(self, level: int) -> None:
        """设置全局日志级别"""
        logging.getLogger().setLevel(level)
    
    def set_log_dir(self, log_dir: str) -> None:
        """设置日志目录"""
        self.log_dir = log_dir
        self._setup_root_logger()


# 全局单例
global_logger = GlobalLogger()


def get_logger(name: str) -> logging.Logger:
    """获取日志器的便捷函数"""
    return global_logger.get_logger(name)