"""Task Scheduler module for periodic execution of auto-thanks tasks."""

import logging
from typing import Callable, Optional
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Use try/except to handle both relative imports (development) and absolute imports (bundled)
try:
    from .models import ScanResult
    from .task_orchestrator import TaskOrchestrator
except ImportError:
    from auto_thanks.models import ScanResult
    from auto_thanks.task_orchestrator import TaskOrchestrator

logger = logging.getLogger(__name__)


class TaskScheduler:
    """定时任务调度器"""

    # Interval bounds (in minutes)
    MIN_INTERVAL = 5
    MAX_INTERVAL = 1440  # 24 hours

    # Job ID for the scheduled task
    JOB_ID = "auto_thanks_scan"

    def __init__(
        self, 
        orchestrator: TaskOrchestrator, 
        interval_minutes: int = 60,
        on_scan_complete: Optional[Callable[[ScanResult], None]] = None
    ):
        """
        初始化调度器

        Args:
            orchestrator: 任务协调器
            interval_minutes: 检查间隔（分钟），默认60分钟
            on_scan_complete: 扫描完成后的回调函数，接收 ScanResult 参数
        """
        self.orchestrator = orchestrator
        self._interval_minutes = self._validate_interval(interval_minutes)
        self._scheduler: Optional[BackgroundScheduler] = None
        self._running = False
        self._last_result: Optional[ScanResult] = None
        self._on_scan_complete = on_scan_complete

    def _validate_interval(self, minutes: int) -> int:
        """
        验证并规范化间隔值

        Args:
            minutes: 输入的间隔分钟数

        Returns:
            规范化后的间隔分钟数（在 MIN_INTERVAL 和 MAX_INTERVAL 之间）
        """
        if minutes < self.MIN_INTERVAL:
            logger.warning(
                f"Interval {minutes} is below minimum, using {self.MIN_INTERVAL} minutes"
            )
            return self.MIN_INTERVAL
        elif minutes > self.MAX_INTERVAL:
            logger.warning(
                f"Interval {minutes} exceeds maximum, using {self.MAX_INTERVAL} minutes"
            )
            return self.MAX_INTERVAL
        return minutes

    def start(self) -> None:
        """启动定时任务"""
        if self._running:
            logger.warning("Scheduler is already running")
            return

        logger.info(f"Starting scheduler with interval: {self._interval_minutes} minutes")
        
        self._scheduler = BackgroundScheduler()
        self._scheduler.add_job(
            self._execute_scan,
            trigger=IntervalTrigger(minutes=self._interval_minutes),
            id=self.JOB_ID,
            name="Auto Thanks Scan",
            replace_existing=True
        )
        self._scheduler.start()
        self._running = True
        
        logger.info("Scheduler started successfully")

    def stop(self) -> None:
        """停止定时任务"""
        if not self._running:
            logger.warning("Scheduler is not running")
            return

        logger.info("Stopping scheduler")
        
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
        
        self._running = False
        logger.info("Scheduler stopped")

    def run_now(self, skip_callback: bool = False) -> ScanResult:
        """
        立即执行一次扫描

        Args:
            skip_callback: 是否跳过扫描完成回调（用于手动执行时避免重复通知）

        Returns:
            扫描结果
        """
        logger.info("Running scan immediately")
        return self._execute_scan(skip_callback=skip_callback)

    def set_interval(self, minutes: int) -> None:
        """
        设置检查间隔

        Args:
            minutes: 新的间隔分钟数
        """
        new_interval = self._validate_interval(minutes)
        
        if new_interval == self._interval_minutes:
            logger.debug(f"Interval unchanged: {new_interval} minutes")
            return
        
        old_interval = self._interval_minutes
        self._interval_minutes = new_interval
        
        logger.info(f"Interval changed from {old_interval} to {new_interval} minutes")
        
        # If scheduler is running, reschedule the job
        if self._running and self._scheduler:
            self._scheduler.reschedule_job(
                self.JOB_ID,
                trigger=IntervalTrigger(minutes=self._interval_minutes)
            )
            logger.info("Job rescheduled with new interval")

    def is_running(self) -> bool:
        """
        检查调度器是否运行中

        Returns:
            True 如果调度器正在运行，否则 False
        """
        return self._running

    def get_interval(self) -> int:
        """
        获取当前间隔设置

        Returns:
            当前间隔分钟数
        """
        return self._interval_minutes

    def get_last_result(self) -> Optional[ScanResult]:
        """
        获取上次扫描结果

        Returns:
            上次扫描结果，如果没有则返回 None
        """
        return self._last_result

    def _execute_scan(self, skip_callback: bool = False) -> ScanResult:
        """
        执行扫描任务

        Args:
            skip_callback: 是否跳过扫描完成回调

        Returns:
            扫描结果
        """
        logger.info(f"Executing scheduled scan at {datetime.now()}")
        
        try:
            result = self.orchestrator.run_scan_cycle()
            self._last_result = result
            
            logger.info(
                f"Scan completed: {result.buttons_clicked} buttons clicked "
                f"({result.failed_clicks} failed), {len(result.errors)} errors"
            )
            
            # Call the scan complete callback if set and not skipped
            if self._on_scan_complete and not skip_callback:
                try:
                    self._on_scan_complete(result)
                except Exception as e:
                    logger.error(f"Error in scan complete callback: {e}")
            
            return result
        except Exception as e:
            logger.error(f"Error during scheduled scan: {e}")
            # Create an error result
            error_result = ScanResult(
                scan_time=datetime.now(),
                errors=[str(e)]
            )
            self._last_result = error_result
            
            # Call the scan complete callback even on error (unless skipped)
            if self._on_scan_complete and not skip_callback:
                try:
                    self._on_scan_complete(error_result)
                except Exception as cb_error:
                    logger.error(f"Error in scan complete callback: {cb_error}")
            
            return error_result

    def set_on_scan_complete(self, callback: Optional[Callable[[ScanResult], None]]) -> None:
        """
        设置扫描完成回调函数

        Args:
            callback: 扫描完成后的回调函数，接收 ScanResult 参数
        """
        self._on_scan_complete = callback
