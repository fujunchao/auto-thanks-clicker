# Auto Thanks Clicker

一个 Windows 桌面自动化工具，用于自动识别特定应用窗口中的"谢谢"按钮并自动点击。

## 功能特点

- 🔍 自动识别目标窗口中的"谢谢"按钮
- 🖱️ 自动点击按钮，将其变为"已感谢"状态
- ⏰ 支持定时自动执行（默认每小时一次）
- 📊 系统托盘图标，方便控制
- 📝 详细的运行日志

## 使用方法

### 1. 准备模板图片

在 `templates` 文件夹中放入模板图片（PNG格式）。模板需要用户自行截图准备，因为不同屏幕分辨率和DPI设置需要不同的模板。

#### 必需模板（缺少任何一个将无法启动）

| 文件名 | 说明 |
|--------|------|
| `thanks_button.png` | "谢谢"按钮的截图 |
| `thanked_button.png` | "已感谢"按钮的截图 |
| `tab_likes.png` | "赞"标签的截图 |
| `tab_follows.png` | "关注"标签的截图 |

#### 可选模板（缺少时使用降级功能）

| 文件名 | 说明 | 缺少时的行为 |
|--------|------|-------------|
| `divider_line.png` | "—以下是更早消息—"分界线的截图 | 处理所有可见的"谢谢"按钮（符合需求3.5） |
| `tab_indicator.png` | "+X"指示器的截图（如"赞+1"） | 按默认顺序处理标签，不进行优先级排序 |

#### 模板截图建议

1. 使用系统截图工具（Win+Shift+S）截取目标元素
2. 确保截图清晰，边界紧凑
3. 保存为 PNG 格式以保持质量
4. 如果识别不准确，尝试调整 `confidence_threshold` 参数

### 2. 配置

编辑 `config.json` 文件：

```json
{
    "window_title": "目标窗口标题",
    "check_interval": 60,
    "scroll_count": 3,
    "click_delay": 0.5,
    "confidence_threshold": 0.8,
    "templates_dir": "templates",
    "log_file": "auto_thanks.log"
}
```

#### 配置参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `window_title` | - | **必须设置**，目标窗口标题关键字 |
| `check_interval` | 60 | 自动检查间隔（分钟），范围 5-1440 |
| `scroll_count` | 3 | 每次扫描的滚动次数 |
| `click_delay` | 0.5 | 点击间隔（秒） |
| `confidence_threshold` | 0.8 | 图像匹配阈值，0.0-1.0 |
| `templates_dir` | templates | 模板图片目录 |
| `log_file` | auto_thanks.log | 日志文件名 |

### 3. 运行

双击 `AutoThanksClicker.exe` 启动程序，程序会在系统托盘显示图标。

右键托盘图标可以：
- 启动/停止自动检查
- 立即执行一次扫描
- 打开设置（配置文件）
- 退出程序

## 开发

### 环境要求

- Python 3.10+
- Windows 10/11

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行测试

```bash
pytest tests/ -v
```

### 打包

```bash
python build.py --clean --verify
```

## 技术栈

- **OpenCV** - 图像模板匹配
- **PyAutoGUI** - 鼠标自动化
- **PyWin32** - Windows 窗口管理
- **Pystray** - 系统托盘图标
- **APScheduler** - 定时任务调度
- **Hypothesis** - 属性测试

## 许可证

MIT License
