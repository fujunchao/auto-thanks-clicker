"""Settings window module for Auto Thanks Clicker."""

import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
import threading

# Use try/except to handle both relative imports (development) and absolute imports (bundled)
try:
    from .models import Config
    from .config_manager import ConfigManager
except ImportError:
    from auto_thanks.models import Config
    from auto_thanks.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class SettingsWindow:
    """设置窗口"""

    WINDOW_TITLE = "Auto Thanks - 设置"
    WINDOW_WIDTH = 400
    WINDOW_HEIGHT = 400
    PADDING = 10

    def __init__(
        self,
        config_manager: ConfigManager,
        on_save: Optional[Callable[[Config], None]] = None
    ):
        """
        初始化设置窗口

        Args:
            config_manager: 配置管理器
            on_save: 保存配置后的回调函数
        """
        self.config_manager = config_manager
        self.on_save = on_save
        self._window: Optional[tk.Tk] = None
        self._is_open = False
        self._lock = threading.Lock()

        # Entry variables
        self._window_title_var: Optional[tk.StringVar] = None
        self._process_name_var: Optional[tk.StringVar] = None
        self._check_interval_var: Optional[tk.StringVar] = None
        self._scroll_count_var: Optional[tk.StringVar] = None
        self._click_delay_var: Optional[tk.StringVar] = None
        self._confidence_var: Optional[tk.StringVar] = None
        self._templates_dir_var: Optional[tk.StringVar] = None

    def show(self) -> None:
        """显示设置窗口"""
        with self._lock:
            if self._is_open:
                logger.info("Settings window already open, skipping")
                return
            self._is_open = True

        logger.info("Opening settings window")
        try:
            self._create_window()
        finally:
            with self._lock:
                self._is_open = False

    def _create_window(self) -> None:
        """创建设置窗口"""
        self._window = tk.Tk()
        self._window.title(self.WINDOW_TITLE)
        self._window.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self._window.resizable(False, False)
        
        # Make window stay on top initially
        self._window.attributes('-topmost', True)
        self._window.update()
        self._window.attributes('-topmost', False)
        
        # Center window on screen
        self._window.update_idletasks()
        x = (self._window.winfo_screenwidth() - self.WINDOW_WIDTH) // 2
        y = (self._window.winfo_screenheight() - self.WINDOW_HEIGHT) // 2
        self._window.geometry(f"+{x}+{y}")

        # Load current config
        config = self.config_manager.load()

        # Create main frame with padding
        main_frame = ttk.Frame(self._window, padding=self.PADDING)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create form fields
        self._create_form_fields(main_frame, config)

        # Create buttons
        self._create_buttons(main_frame)

        # Handle window close
        self._window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Focus the window
        self._window.focus_force()
        
        # Run the mainloop - this blocks until window is closed
        self._window.mainloop()

    def _create_form_fields(self, parent: ttk.Frame, config: Config) -> None:
        """创建表单字段"""
        row = 0

        # Window title
        ttk.Label(parent, text="目标窗口标题:").grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self._window_title_var = tk.StringVar(value=config.window_title)
        ttk.Entry(parent, textvariable=self._window_title_var, width=35).grid(
            row=row, column=1, sticky=tk.EW, pady=5
        )
        row += 1

        # Process name
        ttk.Label(parent, text="目标进程名:").grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self._process_name_var = tk.StringVar(value=config.process_name)
        process_entry = ttk.Entry(parent, textvariable=self._process_name_var, width=35)
        process_entry.grid(row=row, column=1, sticky=tk.EW, pady=5)
        ttk.Label(parent, text="(如 app.exe)", foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=5
        )
        row += 1

        # Check interval
        ttk.Label(parent, text="检查间隔 (分钟):").grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self._check_interval_var = tk.StringVar(value=str(config.check_interval))
        interval_entry = ttk.Entry(
            parent, textvariable=self._check_interval_var, width=35
        )
        interval_entry.grid(row=row, column=1, sticky=tk.EW, pady=5)
        ttk.Label(parent, text="(5-1440)", foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=5
        )
        row += 1

        # Scroll count
        ttk.Label(parent, text="滚动次数:").grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self._scroll_count_var = tk.StringVar(value=str(config.scroll_count))
        ttk.Entry(parent, textvariable=self._scroll_count_var, width=35).grid(
            row=row, column=1, sticky=tk.EW, pady=5
        )
        row += 1

        # Click delay
        ttk.Label(parent, text="点击延迟 (秒):").grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self._click_delay_var = tk.StringVar(value=str(config.click_delay))
        ttk.Entry(parent, textvariable=self._click_delay_var, width=35).grid(
            row=row, column=1, sticky=tk.EW, pady=5
        )
        row += 1

        # Confidence threshold
        ttk.Label(parent, text="匹配置信度:").grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self._confidence_var = tk.StringVar(value=str(config.confidence_threshold))
        confidence_entry = ttk.Entry(
            parent, textvariable=self._confidence_var, width=35
        )
        confidence_entry.grid(row=row, column=1, sticky=tk.EW, pady=5)
        ttk.Label(parent, text="(0.0-1.0)", foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=5
        )
        row += 1

        # Templates directory
        ttk.Label(parent, text="模板目录:").grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self._templates_dir_var = tk.StringVar(value=config.templates_dir)
        ttk.Entry(parent, textvariable=self._templates_dir_var, width=35).grid(
            row=row, column=1, sticky=tk.EW, pady=5
        )
        row += 1

        # Configure column weights
        parent.columnconfigure(1, weight=1)

    def _create_buttons(self, parent: ttk.Frame) -> None:
        """创建按钮"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))

        # Save button
        save_btn = ttk.Button(
            button_frame, text="保存", command=self._on_save, width=10
        )
        save_btn.pack(side=tk.RIGHT, padx=5)

        # Cancel button
        cancel_btn = ttk.Button(
            button_frame, text="取消", command=self._on_close, width=10
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

        # Reset to defaults button
        reset_btn = ttk.Button(
            button_frame, text="恢复默认", command=self._on_reset, width=10
        )
        reset_btn.pack(side=tk.LEFT, padx=5)

    def _validate_config(self) -> Optional[Config]:
        """
        验证并创建配置对象

        Returns:
            有效的 Config 对象，验证失败返回 None
        """
        try:
            # Parse and validate check interval
            check_interval = int(self._check_interval_var.get())
            if check_interval < 5 or check_interval > 1440:
                messagebox.showerror(
                    "验证错误", "检查间隔必须在 5-1440 分钟之间"
                )
                return None

            # Parse and validate scroll count
            scroll_count = int(self._scroll_count_var.get())
            if scroll_count < 0:
                messagebox.showerror("验证错误", "滚动次数不能为负数")
                return None

            # Parse and validate click delay
            click_delay = float(self._click_delay_var.get())
            if click_delay < 0:
                messagebox.showerror("验证错误", "点击延迟不能为负数")
                return None

            # Parse and validate confidence threshold
            confidence = float(self._confidence_var.get())
            if confidence < 0.0 or confidence > 1.0:
                messagebox.showerror(
                    "验证错误", "匹配置信度必须在 0.0-1.0 之间"
                )
                return None

            return Config(
                window_title=self._window_title_var.get(),
                process_name=self._process_name_var.get(),
                check_interval=check_interval,
                scroll_count=scroll_count,
                click_delay=click_delay,
                confidence_threshold=confidence,
                templates_dir=self._templates_dir_var.get()
            )

        except ValueError as e:
            messagebox.showerror("验证错误", f"请输入有效的数值: {e}")
            return None

    def _on_save(self) -> None:
        """保存配置"""
        config = self._validate_config()
        if config is None:
            return

        try:
            self.config_manager.save(config)
            logger.info("Configuration saved successfully")
            
            if self.on_save:
                self.on_save(config)
            
            messagebox.showinfo("成功", "配置已保存")
            self._on_close()
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            messagebox.showerror("错误", f"保存配置失败: {e}")

    def _on_reset(self) -> None:
        """恢复默认配置"""
        if messagebox.askyesno("确认", "确定要恢复默认配置吗？"):
            default_config = self.config_manager.get_default_config()
            self._window_title_var.set(default_config.window_title)
            self._process_name_var.set(default_config.process_name)
            self._check_interval_var.set(str(default_config.check_interval))
            self._scroll_count_var.set(str(default_config.scroll_count))
            self._click_delay_var.set(str(default_config.click_delay))
            self._confidence_var.set(str(default_config.confidence_threshold))
            self._templates_dir_var.set(default_config.templates_dir)
            logger.info("Configuration reset to defaults")

    def _on_close(self) -> None:
        """关闭窗口"""
        logger.info("Closing settings window")
        if self._window:
            self._window.quit()  # Exit mainloop
            self._window.destroy()
            self._window = None

    def is_open(self) -> bool:
        """
        检查窗口是否打开

        Returns:
            True 如果窗口已打开
        """
        with self._lock:
            return self._is_open
