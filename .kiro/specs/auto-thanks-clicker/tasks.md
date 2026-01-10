# Implementation Plan: Auto Thanks Clicker

## Overview

本实现计划将设计文档转化为可执行的编码任务。采用自底向上的方式，先实现基础模块，再逐步集成。使用 Python 3.10+ 开发，pytest + hypothesis 进行测试。

## Tasks

- [x] 1. 项目初始化和基础设施
  - [x] 1.1 创建项目目录结构和虚拟环境
    - 创建 `src/auto_thanks/` 包目录
    - 创建 `tests/` 测试目录
    - 创建 `templates/` 模板图片目录
    - 创建 `requirements.txt` 依赖文件
    - _Requirements: 7.4, 8.1_
  - [x] 1.2 实现数据模型和配置类
    - 实现 `Config` dataclass
    - 实现 `MatchResult` dataclass
    - 实现 `ScanResult` dataclass
    - _Requirements: 7.4_
  - [x] 1.3 实现 ConfigManager 配置管理模块
    - 实现 `load()` 方法从 JSON 加载配置
    - 实现 `save()` 方法保存配置到 JSON
    - 实现 `get_default_config()` 方法
    - _Requirements: 7.4_
  - [x] 1.4 编写 ConfigManager 属性测试
    - **Property 9: Configuration Round-Trip Consistency**
    - **Validates: Requirements 7.4**

- [x] 2. 窗口捕获模块
  - [x] 2.1 实现 WindowCapture 类
    - 实现 `find_window()` 使用 win32gui.FindWindow
    - 实现 `get_window_rect()` 获取窗口位置
    - 实现 `capture_screenshot()` 使用 win32ui 截图
    - 实现 `is_window_visible()` 检查窗口可见性
    - 实现 `bring_to_front()` 将窗口置前
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  - [x] 2.2 编写 WindowCapture 属性测试
    - **Property 1: Window Finding Correctness**
    - **Property 2: Screenshot Dimension Consistency**
    - **Validates: Requirements 1.1, 1.2, 1.3**

- [x] 3. Checkpoint - 基础模块验证
  - 确保所有测试通过，如有问题请询问用户

- [x] 4. 图像识别模块
  - [x] 4.1 实现 ImageRecognizer 类基础功能
    - 实现 `load_templates()` 加载模板图片
    - 实现 `find_template()` 使用 OpenCV 模板匹配
    - _Requirements: 3.1, 3.2_
  - [x] 4.2 实现按钮和分界线识别方法
    - 实现 `find_thanks_buttons()` 查找谢谢按钮
    - 实现 `find_thanked_buttons()` 查找已感谢按钮
    - 实现 `find_divider_line()` 查找分界线
    - 实现 `find_tab_buttons()` 查找标签页按钮
    - _Requirements: 2.1, 3.1, 3.2, 3.4_
  - [x] 4.3 实现按钮过滤方法
    - 实现 `filter_buttons_above_divider()` 过滤分界线上方按钮
    - _Requirements: 3.3, 3.5_
  - [x] 4.4 编写 ImageRecognizer 属性测试
    - **Property 3: Template Matching Completeness**
    - **Property 4: Button Filtering by Divider Position**
    - **Property 5: Thanks vs Thanked Button Classification**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

- [x] 5. 自动点击模块
  - [x] 5.1 实现 AutoClicker 类
    - 实现 `click_at()` 在指定位置点击
    - 实现 `click_button()` 点击匹配到的按钮
    - 实现 `scroll_down()` 向下滚动
    - 实现 `scroll_up()` 向上滚动（刷新）
    - _Requirements: 4.1, 4.4, 5.1, 5.2, 5.4_
  - [x] 5.2 编写 AutoClicker 属性测试
    - **Property 6: Click Coordinate Calculation**
    - **Property 7: Scroll Position Bounds**
    - **Validates: Requirements 4.1, 4.4, 5.2**

- [x] 6. Checkpoint - 核心模块验证
  - 确保所有测试通过，如有问题请询问用户

- [x] 7. 任务协调模块
  - [x] 7.1 实现 TaskOrchestrator 类
    - 实现 `run_scan_cycle()` 执行完整扫描周期
    - 实现 `process_tab()` 处理单个标签页
    - 实现 `refresh_content()` 刷新内容
    - _Requirements: 2.2, 2.3, 2.4, 4.1, 4.3, 4.4_
  - [x] 7.2 编写 TaskOrchestrator 单元测试
    - 测试扫描流程逻辑
    - 测试标签页切换逻辑
    - _Requirements: 2.2, 2.3, 4.1, 4.3_

- [x] 8. 调度器模块
  - [x] 8.1 实现 TaskScheduler 类
    - 实现 `start()` 启动定时任务
    - 实现 `stop()` 停止定时任务
    - 实现 `run_now()` 立即执行
    - 实现 `set_interval()` 设置间隔（含验证）
    - 实现 `is_running()` 检查运行状态
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  - [x] 8.2 编写 TaskScheduler 属性测试
    - **Property 8: Interval Configuration Validation**
    - **Validates: Requirements 6.2**

- [x] 9. 日志模块
  - [x] 9.1 实现日志配置
    - 配置日志格式和输出
    - 实现日志文件轮转
    - _Requirements: 8.1, 8.2, 8.3_

- [x] 10. Checkpoint - 后端模块验证
  - 确保所有测试通过，如有问题请询问用户

- [x] 11. 用户界面模块
  - [x] 11.1 实现 TrayIcon 系统托盘
    - 使用 pystray 创建托盘图标
    - 实现右键菜单（启动、停止、设置、退出）
    - 实现状态图标更新
    - 实现通知显示
    - _Requirements: 7.1, 7.2, 7.5_
  - [x] 11.2 实现设置窗口
    - 使用 tkinter 创建设置界面
    - 实现配置项编辑和保存
    - _Requirements: 7.3_

- [x] 12. 主程序入口
  - [x] 12.1 实现主程序
    - 创建 `main.py` 入口文件
    - 初始化所有模块
    - 启动托盘图标和调度器
    - _Requirements: 6.4, 6.5, 7.1_

- [x] 13. 打包和分发
  - [x] 13.1 配置 PyInstaller 打包
    - 创建 `.spec` 打包配置文件
    - 打包为单个 `.exe` 文件
    - 包含空的 templates 目录结构（用户需自行准备模板图片）
    - 包含默认配置文件
    - 注: templates/ 目录故意为空，因为模板需要用户根据自己的屏幕分辨率截图准备
    - _Requirements: 7.1_

- [x] 14. Final Checkpoint - 完整功能验证
  - 确保所有测试通过
  - 验证打包后的程序可正常运行
  - 如有问题请询问用户

---

## Bug Fixes (Codex Audit)

以下任务用于修复 Codex 代码审核发现的问题：

- [x] 15. [High] 点击后验证按钮状态变化
  - [x] 15.1 修改 TaskOrchestrator.process_tab() 添加点击后验证逻辑
    - 点击按钮后重新截图检查按钮是否变为"已感谢"
    - 如果状态未变化，记录警告日志并跳过
    - 添加可配置的验证等待时间
    - _Requirements: 4.2, 4.5_
  - [x] 15.2 添加相关单元测试
    - 测试点击后状态验证逻辑
    - 测试状态未变化时的警告日志
    - _Requirements: 4.2, 4.5_

- [x] 16. [High] 窗口最小化/隐藏时等待可见
  - [x] 16.1 修改 TaskOrchestrator.run_scan_cycle() 添加等待窗口可见逻辑
    - 当窗口不可见时，循环等待直到可见或超时
    - 添加可配置的等待超时时间（默认30秒）
    - 超时后记录错误并返回
    - _Requirements: 1.4_
  - [x] 16.2 修改 WindowCapture.find_window() 支持查找最小化窗口
    - 移除 IsWindowVisible 过滤，允许找到最小化窗口
    - 添加 wait_for_visible() 方法
    - _Requirements: 1.4_
  - [x] 16.3 添加相关单元测试
    - 测试等待窗口可见逻辑
    - 测试超时处理
    - _Requirements: 1.4_

- [x] 17. [Medium] 支持进程名匹配窗口
  - [x] 17.1 修改 WindowCapture 添加进程名匹配支持
    - 添加 process_name 参数
    - 实现 find_window_by_process() 方法
    - 修改 find_window() 支持标题或进程名匹配
    - _Requirements: 1.1_
  - [x] 17.2 更新 Config 和 ConfigManager 支持进程名配置
    - 添加 process_name 配置项
    - 更新设置窗口支持进程名输入
    - _Requirements: 1.1, 7.3_
  - [x] 17.3 添加相关单元测试
    - 测试进程名匹配逻辑
    - _Requirements: 1.1_

- [x] 18. [Medium] 实现"+X"指示器优先级逻辑
  - [x] 18.1 添加 tab_indicator.png 模板支持
    - 在 ImageRecognizer 中添加 TEMPLATE_TAB_INDICATOR 常量
    - 实现 find_tab_indicators() 方法检测"+X"指示器
    - _Requirements: 2.2_
  - [x] 18.2 修改 TaskOrchestrator 实现标签优先级
    - 修改 run_scan_cycle() 先检测哪个标签有"+X"指示器
    - 优先处理有指示器的标签
    - _Requirements: 2.2_
  - [x] 18.3 添加相关单元测试
    - 测试指示器检测逻辑
    - 测试标签优先级排序
    - _Requirements: 2.2_

- [x] 19. [Medium] 打包模式下正确显示设置窗口
  - [x] 19.1 修改 main.py 的 _show_settings() 方法
    - 打包模式下也使用 SettingsWindow 而非打开配置文件
    - 使用线程安全的方式显示 tkinter 窗口
    - _Requirements: 7.3_
  - [x] 19.2 验证打包后设置窗口正常工作
    - 测试打包后点击"设置"菜单
    - _Requirements: 7.3_

- [x] 20. [Medium] 模板目录不存在时显式报错
  - [x] 20.1 修改 ImageRecognizer.load_templates() 添加启动检查
    - 如果模板目录不存在，抛出异常而非仅记录警告
    - 提供清晰的错误消息提示用户准备模板图片
    - _Requirements: 设计文档错误处理_
  - [x] 20.2 修改 main.py 初始化时捕获并显示模板错误
    - 显示用户友好的错误对话框
    - _Requirements: 设计文档错误处理_

- [x] 21. [Low] 定时扫描完成后显示通知
  - [x] 21.1 修改 TaskScheduler 添加扫描完成回调
    - 添加 on_scan_complete 回调参数
    - 在 _execute_scan() 完成后调用回调
    - _Requirements: 7.5_
  - [x] 21.2 修改 main.py 连接扫描完成通知
    - 在初始化时设置回调显示通知
    - 只在有按钮被点击时显示通知
    - _Requirements: 7.5_

- [x] 22. [Low] 滚动位置限制在内容区域
  - [x] 22.1 修改 TaskOrchestrator.refresh_content() 计算内容区域
    - 根据标签页位置估算内容区域边界
    - 滚动位置限制在内容区域内
    - _Requirements: 5.2_
  - [x] 22.2 添加相关单元测试
    - 测试滚动位置边界计算
    - _Requirements: 5.2_

- [x] 23. Checkpoint - Bug 修复验证
  - 确保所有测试通过
  - 验证修复后的功能正常工作
  - 如有问题请询问用户

---

## Bug Fixes (Codex Audit Round 2)

以下任务用于修复 Codex 第二轮代码审核发现的问题：

- [x] 24. [High] psutil 依赖未声明
  - [x] 24.1 在 requirements.txt 中添加 psutil 依赖
    - 添加 `psutil>=5.9.0` 到依赖列表
    - _Requirements: 1.1_
  - [x] 24.2 在 auto_thanks.spec 中添加 psutil 到 hiddenimports
    - 确保打包时包含 psutil 模块
    - _Requirements: 1.1_

- [x] 25. [High] 点击验证截图失败时应视为失败并记录
  - [x] 25.1 在 ScanResult 模型中添加 failed_clicks 字段
    - 添加 `failed_clicks: int = 0` 字段用于记录验证失败的点击数
    - _Requirements: 4.2, 4.5_
  - [x] 25.2 修改 TaskOrchestrator._verify_button_state_changed()
    - 截图失败时返回 False 而非 True
    - 记录错误日志说明验证失败原因
    - _Requirements: 4.2, 4.5_
  - [x] 25.3 修改 TaskOrchestrator.process_tab() 统计失败点击
    - 验证失败时增加 failed_clicks 计数
    - 返回值改为 (found, clicked, failed) 三元组
    - _Requirements: 4.2, 4.5_
  - [x] 25.4 修改 TaskOrchestrator.run_scan_cycle() 汇总失败点击
    - 汇总各标签页的 failed_clicks 到 ScanResult
    - _Requirements: 4.2, 4.5_
  - [x] 25.5 更新相关单元测试
    - 修改测试期望：截图失败应返回 False
    - 测试 failed_clicks 统计逻辑
    - _Requirements: 4.2, 4.5_

- [x] 26. [Medium] 模板检查应验证必需模板文件存在
  - [x] 26.1 修改 ImageRecognizer.load_templates() 验证必需模板
    - 定义必需模板列表（thanks_button.png, thanked_button.png）
    - 检查必需模板是否存在，不存在则抛出异常
    - 提供清晰的错误消息列出缺失的模板
    - _Requirements: 设计文档错误处理_
  - [x] 26.2 添加相关单元测试
    - 测试缺失必需模板时抛出异常
    - _Requirements: 设计文档错误处理_

- [x] 27. [Low] 刷新应使用向下滚动而非先向上再向下
  - [x] 27.1 修改 TaskOrchestrator.refresh_content()
    - 移除 scroll_up 调用
    - 只使用 scroll_down 触发刷新
    - _Requirements: 5.1_
  - [x] 27.2 更新相关单元测试
    - 验证只调用 scroll_down
    - _Requirements: 5.1_

- [x] 28. [Low] 手动"立即执行"避免重复通知
  - [x] 28.1 修改 TrayIcon._on_run_now() 避免重复通知
    - 添加 skip_callback 参数到 scheduler.run_now()
    - 手动执行时跳过 on_scan_complete 回调
    - 只在 _on_run_now 中显示一次通知
    - _Requirements: 7.5_
  - [x] 28.2 修改 TaskScheduler.run_now() 支持跳过回调
    - 添加 skip_callback 参数（默认 False）
    - 当 skip_callback=True 时不调用 on_scan_complete
    - _Requirements: 7.5_

- [x] 29. Checkpoint - Bug 修复验证 (Round 2)
  - 确保所有测试通过
  - 验证修复后的功能正常工作
  - 如有问题请询问用户

---

## Bug Fixes (Codex Audit Round 3)

以下任务用于修复 Codex 第三轮代码审核发现的问题：

- [x] 30. [High] 必需模板列表应包含标签页模板
  - [x] 30.1 修改 ImageRecognizer.REQUIRED_TEMPLATES 添加标签页模板
    - 添加 tab_likes.png 和 tab_follows.png 到必需模板列表
    - 这是满足需求 2.1 的必要条件
    - _Requirements: 2.1_
  - [x] 30.2 更新错误消息说明所有必需模板
    - 在 TemplateDirectoryError 消息中列出所有必需模板
    - _Requirements: 2.1_
  - [x] 30.3 更新相关单元测试
    - 测试缺失标签页模板时抛出异常
    - _Requirements: 2.1_

- [x] 31. [Low] 扫描汇总日志应包含 failed_clicks
  - [x] 31.1 修改 TaskOrchestrator.run_scan_cycle() 日志输出
    - 在扫描完成日志中包含 failed_clicks 数量
    - 格式: "Scan complete: X/Y buttons clicked (Z failed) in N tabs"
    - _Requirements: 8.1_
    - 注: 此功能已在之前的修复中实现
  - [x] 31.2 修改 TaskScheduler._execute_scan() 日志输出
    - 在调度器日志中也包含 failed_clicks
    - _Requirements: 8.1_

- [x] 32. Checkpoint - Bug 修复验证 (Round 3)
  - 确保所有测试通过
  - 验证修复后的功能正常工作
  - 如有问题请询问用户

- [x] 33. 文档更新 - 明确模板设计决策
  - [x] 33.1 更新 ImageRecognizer 代码注释
    - 添加 OPTIONAL_TEMPLATES 常量并说明降级行为
    - 更新错误消息区分必需和可选模板
    - 添加可选模板缺失时的日志提示
    - _Requirements: 2.2, 3.2, 3.5_
  - [x] 33.2 更新 README.md 模板说明
    - 区分必需模板和可选模板
    - 说明可选模板缺失时的降级行为
    - 添加模板截图建议
    - _Requirements: 文档_
  - [x] 33.3 更新 design.md 模板目录结构说明
    - 标注每个模板的必需/可选状态
    - 添加设计决策说明
    - _Requirements: 文档_
  - [x] 33.4 更新 tasks.md 打包任务说明
    - 说明 templates/ 目录故意为空的原因
    - _Requirements: 文档_

## Notes

- 所有任务均为必做任务，确保完整测试覆盖
- 每个任务都引用了具体的需求条款以便追溯
- Checkpoint 任务用于阶段性验证
- 属性测试验证核心正确性属性
- 单元测试覆盖边界情况和错误处理
