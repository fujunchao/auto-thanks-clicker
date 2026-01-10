"""Data models for Auto Thanks Clicker."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class Config:
    """应用配置"""
    window_title: str = ""
    process_name: str = ""  # 目标进程名（如 "notepad.exe"）
    check_interval: int = 60  # 检查间隔（分钟）
    scroll_count: int = 3  # 滚动次数
    click_delay: float = 0.5  # 点击延迟（秒）
    confidence_threshold: float = 0.8  # 匹配置信度
    templates_dir: str = "templates"  # 模板目录
    log_file: str = "auto_thanks.log"  # 日志文件
    click_verify_wait: float = 0.3  # 点击后验证等待时间（秒）
    window_visible_timeout: float = 30.0  # 等待窗口可见超时时间（秒）


@dataclass
class MatchResult:
    """模板匹配结果"""
    x: int  # 中心点 X 坐标
    y: int  # 中心点 Y 坐标
    width: int  # 匹配区域宽度
    height: int  # 匹配区域高度
    confidence: float  # 匹配置信度
    template_name: str  # 模板名称


@dataclass
class ScanResult:
    """扫描结果"""
    scan_time: datetime
    tabs_checked: List[str] = field(default_factory=list)
    buttons_found: int = 0
    buttons_clicked: int = 0
    failed_clicks: int = 0  # 验证失败的点击数
    errors: List[str] = field(default_factory=list)
