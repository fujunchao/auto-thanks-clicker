"""Configuration management module for Auto Thanks Clicker."""

import json
import os
from dataclasses import asdict
from typing import Optional

# Use try/except to handle both relative imports (development) and absolute imports (bundled)
try:
    from .models import Config
except ImportError:
    from auto_thanks.models import Config


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str = "config.json"):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path

    def load(self) -> Config:
        """
        从 JSON 文件加载配置
        
        Returns:
            Config 对象，如果文件不存在或无效则返回默认配置
        """
        if not os.path.exists(self.config_path):
            return self.get_default_config()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Config(**data)
        except (json.JSONDecodeError, TypeError, KeyError):
            return self.get_default_config()

    def save(self, config: Config) -> None:
        """
        保存配置到 JSON 文件
        
        Args:
            config: 要保存的配置对象
        """
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(config), f, indent=4, ensure_ascii=False)

    def get_default_config(self) -> Config:
        """
        获取默认配置
        
        Returns:
            默认的 Config 对象
        """
        return Config()
