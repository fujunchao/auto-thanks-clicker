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
    - 包含模板图片和默认配置
    - _Requirements: 7.1_

- [x] 14. Final Checkpoint - 完整功能验证
  - 确保所有测试通过
  - 验证打包后的程序可正常运行
  - 如有问题请询问用户

## Notes

- 所有任务均为必做任务，确保完整测试覆盖
- 每个任务都引用了具体的需求条款以便追溯
- Checkpoint 任务用于阶段性验证
- 属性测试验证核心正确性属性
- 单元测试覆盖边界情况和错误处理
