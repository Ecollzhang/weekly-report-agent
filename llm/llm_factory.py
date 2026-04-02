# llm/llm_factory.py

import os
from typing import Tuple, Optional
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_openai import ChatOpenAI


def get_llm(
    provider: str="",
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000
) -> Tuple[str, object]:
    """
    获取 LLM 实例
    
    Args:
        provider: 模型提供商，支持 "tongyi" 和 "openai"
        model_name: 模型名称，不传则从环境变量读取
        api_key: API Key，不传则从环境变量读取
        api_url: API Base URL，不传则使用默认
        temperature: 温度参数
        max_tokens: 最大输出 token 数
    
    Returns:
        (model_name, llm_instance)
    """
    provider = provider.lower() if provider else os.getenv("PROVIDER", "tongyi").lower()
    if provider == "tongyi":
        # 阿里云通义千问
        model_name = model_name or os.getenv("MODEL_NAME", "qwen-plus")
        api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        
        llm = ChatTongyi(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            dashscope_api_key=api_key,
        )
        return model_name, llm
    
    elif provider == "openai":
        # OpenAI 兼容接口
        model_name = model_name or os.getenv("OPENAI_MODEL", "gpt-4")
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        api_url = api_url or os.getenv("OPENAI_API_BASE")
        
        kwargs = {
            "model": model_name,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "api_key": api_key,
        }
        if api_url:
            kwargs["base_url"] = api_url
        
        llm = ChatOpenAI(**kwargs)
        return model_name, llm
    
    else:
        raise ValueError(f"Unsupported provider: {provider}. Supported: tongyi, openai")


def get_llm_by_config(config: dict) -> Tuple[str, object]:
    """
    根据配置字典获取 LLM
    
    Args:
        config: 配置字典，包含 provider, model_name, api_key, api_url, temperature, max_tokens
        
    Returns:
        (model_name, llm_instance)
    """
    provider = config.get("provider", "tongyi")
    model_name = config.get("model_name")
    api_key = config.get("api_key")
    api_url = config.get("api_url")
    temperature = config.get("temperature", 0.7)
    max_tokens = config.get("max_tokens", 2000)
    
    return get_llm(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        api_url=api_url,
        temperature=temperature,
        max_tokens=max_tokens
    )


def get_default_llm() -> Tuple[str, object]:
    """获取默认 LLM（从环境变量读取配置）"""
    provider = os.getenv("LLM_PROVIDER", "tongyi")
    return get_llm(provider=provider)