"""Standalone settings application for Auto Thanks Clicker.

This module provides a standalone settings window that can be run
as a separate process to avoid tkinter threading issues.
"""

import sys
import os
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

# Setup path for imports
if getattr(sys, 'frozen', False):
    # Running from PyInstaller bundle
    base_path = os.path.dirname(sys.executable)
else:
    # Running in development
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add src to path if needed
src_path = os.path.join(base_path, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    from auto_thanks.models import Config
    from auto_thanks.config_manager import ConfigManager
except ImportError:
    # Fallback for bundled app
    from models import Config
    from config_manager import ConfigManager

logger = logging.getLogger(__name__)


class SettingsApp:
    """独立设置应用"""

    WINDOW_TITLE = "Auto Thanks - 设置"
    WINDOW_WIDTH = 450
    WINDOW_HEIGHT = 380
    PADDING = 15

    def __init__(self, config_path: str):
        """
        初始化设置应用

        Args:
            config_path: 配置文件路径
        """
        self.config_manager = ConfigManager(config_path)
        self._window: Optional[tk.Tk] = None

        # Entry variables
        self._window_title_var: Optional[tk.StringVar] = None
        self._check_interval_var: Optional[tk.StringVar] = None
        self._scroll_count_var: Optional[tk.StringVar] = None
        self._click_delay_var: Optional[tk.StringVar] = None
        self._confidence_var: Optional[tk.StringVar] = None
        self._templates_dir_var: Optional[tk.StringVar] = None

    def run(self) -> None:
        """运行设置窗口"""
        self._create_window()

    def _create_window(self) -> None:
        """创建设置窗口"""
        self._window = tk.Tk()
        self._window.title(self.WINDOW_TITLE)
        self._window.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self._window.resizable(False, False)
        
        # Make window stay on top
        self._window.attributes('-topmost', True)
        
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
        
        # Run the mainloop
        self._window.mainloop()

    def _create_form_fields(self, parent: ttk.Frame, config: Config) -> None:
        """创建表单字段"""
        row = 0

        # Title label
        title_label = ttk.Label(parent, text="Auto Thanks 设置", font=('', 12, 'bold'))
        title_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 15))
        row += 1

        # Window title
        ttk.Label(parent, text="目标窗口标题:").grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self._window_title_var = tk.StringVar(value=config.window_title)
        entry = ttk.Entry(parent, textvariable=self._window_title_var, width=30)
        entry.grid(row=row, column=1, sticky=tk.EW, pady=5, padx=(5, 0))
        ttk.Label(parent, text="(窗口标题关键字)", foreground="gray", font=('', 8)).grid(
            row=row, column=2, sticky=tk.W, padx=5
        )
        row += 1

        # Check interval
        ttk.Label(parent, text="检查间隔 (分钟):").grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self._check_interval_var = tk.StringVar(value=str(config.check_interval))
        ttk.Entry(parent, textvariable=self._check_interval_var, width=30).grid(
            row=row, column=1, sticky=tk.EW, pady=5, padx=(5, 0)
        )
        ttk.Label(parent, text="(5-1440)", foreground="gray", font=('', 8)).grid(
            row=row, column=2, sticky=tk.W, padx=5
        )
        row += 1

        # Scroll count
        ttk.Label(parent, text="滚动次数:").grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self._scroll_count_var = tk.StringVar(value=str(config.scroll_count))
        ttk.Entry(parent, textvariable=self._scroll_count_var, width=30).grid(
            row=row, column=1, sticky=tk.EW, pady=5, padx=(5, 0)
        )
        row += 1

        # Click delay
        ttk.Label(parent, text="点击延迟 (秒):").grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self._click_delay_var = tk.StringVar(value=str(config.click_delay))
        ttk.Entry(parent, textvariable=self._click_delay_var, width=30).grid(
            row=row, column=1, sticky=tk.EW, pady=5, padx=(5, 0)
        )
        row += 1

        # Confidence threshold
        ttk.Label(parent, text="匹配置信度:").grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self._confidence_var = tk.StringVar(value=str(config.confidence_threshold))
        ttk.Entry(parent, textvariable=self._confidence_var, width=30).grid(
            row=row, column=1, sticky=tk.EW, pady=5, padx=(5, 0)
        )
        ttk.Label(parent, text="(0.0-1.0)", foreground="gray", font=('', 8)).grid(
            row=row, column=2, sticky=tk.W, padx=5
        )
        row += 1

        # Templates directory
        ttk.Label(parent, text="模板目录:").grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self._templates_dir_var = tk.StringVar(value=config.templates_dir)
        ttk.Entry(parent, textvariable=self._templates_dir_var, width=30).grid(
            row=row, column=1, sticky=tk.EW, pady=5, padx=(5, 0)
        )
        row += 1

        # Help text
        help_text = ttk.Label(
            parent, 
            text="提示: 目标窗口标题是要监控的应用窗口的标题关键字。\n程序会查找包含该关键字的窗口。",
            foreground="gray",
            font=('', 8)
        )
        help_text.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(15, 0))
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
        """验证并创建配置对象"""
        try:
            window_title = self._window_title_var.get().strip()
            if not window_title:
                messagebox.showwarning("警告", "请输入目标窗口标题")
                return None

            check_interval = int(self._check_interval_var.get())
            if check_interval < 5 or check_interval > 1440:
                messagebox.showerror("验证错误", "检查间隔必须在 5-1440 分钟之间")
                return None

            scroll_count = int(self._scroll_count_var.get())
            if scroll_count < 0:
                messagebox.showerror("验证错误", "滚动次数不能为负数")
                return None

            click_delay = float(self._click_delay_var.get())
            if click_delay < 0:
                messagebox.showerror("验证错误", "点击延迟不能为负数")
                return None

            confidence = float(self._confidence_var.get())
            if confidence < 0.0 or confidence > 1.0:
                messagebox.showerror("验证错误", "匹配置信度必须在 0.0-1.0 之间")
                return None

            return Config(
                window_title=window_title,
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
            messagebox.showinfo("成功", "配置已保存\n\n请重启程序以应用新配置。")
            self._on_close()
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {e}")

    def _on_reset(self) -> None:
        """恢复默认配置"""
        if messagebox.askyesno("确认", "确定要恢复默认配置吗？"):
            default_config = self.config_manager.get_default_config()
            self._window_title_var.set(default_config.window_title)
            self._check_interval_var.set(str(default_config.check_interval))
            self._scroll_count_var.set(str(default_config.scroll_count))
            self._click_delay_var.set(str(default_config.click_delay))
            self._confidence_var.set(str(default_config.confidence_threshold))
            self._templates_dir_var.set(default_config.templates_dir)

    def _on_close(self) -> None:
        """关闭窗口"""
        if self._window:
            self._window.quit()
            self._window.destroy()
            self._window = None


def main():
    """主入口"""
    # Determine config path
    if getattr(sys, 'frozen', False):
        config_path = os.path.join(os.path.dirname(sys.executable), 'config.json')
    else:
        config_path = os.path.join(base_path, 'config.json')
    
    # Allow override via command line
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    app = SettingsApp(config_path)
    app.run()


if __name__ == "__main__":
    main()
