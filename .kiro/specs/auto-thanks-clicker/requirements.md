# Requirements Document

## Introduction

本项目是一个 Windows 桌面自动化工具，用于自动识别特定应用窗口中的"谢谢"按钮并自动点击，将其变为"已感谢"状态。该工具通过图像识别技术定位目标元素，并模拟鼠标操作完成自动感谢功能。

## Glossary

- **Target_Window**: 需要监控的目标应用窗口
- **Thanks_Button**: 显示"谢谢"文字的可点击按钮，点击后变为"已感谢"
- **Thanked_Button**: 显示"已感谢"文字的按钮，表示已完成感谢操作
- **Divider_Line**: "—以下是更早消息—"分界线，用于区分新旧消息
- **Tab_Area**: 包含"赞"和"关注"标签的区域
- **Image_Recognizer**: 图像识别模块，用于识别窗口中的UI元素
- **Auto_Clicker**: 自动点击模块，用于模拟鼠标点击操作
- **Scheduler**: 定时调度模块，用于每小时自动执行检查任务

## Requirements

### Requirement 1: 窗口捕获与识别

**User Story:** As a user, I want the tool to capture and recognize the target application window, so that it can locate the UI elements for automation.

#### Acceptance Criteria

1. WHEN the tool starts, THE Target_Window SHALL be located by window title or process name
2. WHEN the Target_Window is found, THE Image_Recognizer SHALL capture a screenshot of the window content
3. IF the Target_Window is not found, THEN THE tool SHALL log an error message and retry after a configurable interval
4. WHEN the Target_Window is minimized or hidden, THE tool SHALL wait until it becomes visible before proceeding

### Requirement 2: 标签页识别与切换

**User Story:** As a user, I want the tool to recognize and switch between "赞" and "关注" tabs, so that it can check both areas for new thanks opportunities.

#### Acceptance Criteria

1. WHEN scanning for thanks buttons, THE Image_Recognizer SHALL first locate the Tab_Area containing "赞" and "关注" tabs
2. WHEN a tab shows a "+X" indicator (e.g., "赞+1"), THE tool SHALL prioritize checking that tab first
3. WHEN checking multiple tabs, THE Auto_Clicker SHALL click on each tab sequentially to switch views
4. WHEN a tab is clicked, THE tool SHALL wait for the content to load before scanning for Thanks_Buttons

### Requirement 3: 谢谢按钮识别

**User Story:** As a user, I want the tool to accurately identify "谢谢" buttons that need to be clicked, so that I don't miss any new likes or follows.

#### Acceptance Criteria

1. WHEN scanning the window content, THE Image_Recognizer SHALL identify all Thanks_Buttons displaying "谢谢" text
2. WHEN scanning the window content, THE Image_Recognizer SHALL identify the Divider_Line "—以下是更早消息—"
3. THE Image_Recognizer SHALL only return Thanks_Buttons that appear above the Divider_Line
4. THE Image_Recognizer SHALL distinguish between Thanks_Button ("谢谢") and Thanked_Button ("已感谢")
5. IF no Divider_Line is found, THEN THE Image_Recognizer SHALL process all visible Thanks_Buttons

### Requirement 4: 自动点击操作

**User Story:** As a user, I want the tool to automatically click "谢谢" buttons, so that they become "已感谢" without manual intervention.

#### Acceptance Criteria

1. WHEN a Thanks_Button is identified, THE Auto_Clicker SHALL click it exactly once
2. WHEN a Thanks_Button is clicked, THE tool SHALL wait for the button to change to Thanked_Button before proceeding
3. THE Auto_Clicker SHALL NOT click on Thanked_Buttons to avoid toggling back to "谢谢"
4. WHEN multiple Thanks_Buttons are found, THE Auto_Clicker SHALL process them one by one with a configurable delay between clicks
5. IF a click fails to change the button state, THEN THE tool SHALL log a warning and skip to the next button

### Requirement 5: 内容刷新与滚动

**User Story:** As a user, I want the tool to refresh content by scrolling, so that it can detect newly added items.

#### Acceptance Criteria

1. WHEN starting a scan cycle, THE Auto_Clicker SHALL perform a mouse scroll down gesture to trigger content refresh
2. WHEN scrolling, THE tool SHALL scroll within the content area only, not affecting other parts of the window
3. WHEN content is refreshed, THE tool SHALL wait for loading to complete before scanning
4. THE tool SHALL scroll down a configurable number of times to load more content before scanning

### Requirement 6: 定时自动执行

**User Story:** As a user, I want the tool to automatically check for new thanks opportunities every hour, so that I don't have to manually trigger it.

#### Acceptance Criteria

1. THE Scheduler SHALL execute the scan and click cycle every hour by default
2. THE Scheduler SHALL allow configuration of the check interval (minimum 5 minutes, maximum 24 hours)
3. WHEN a scheduled check starts, THE tool SHALL log the start time and results
4. THE Scheduler SHALL continue running in the background until manually stopped
5. WHEN the tool is restarted, THE Scheduler SHALL resume with the configured interval

### Requirement 7: 用户界面与配置

**User Story:** As a user, I want a simple interface to configure and control the tool, so that I can customize its behavior.

#### Acceptance Criteria

1. THE tool SHALL provide a system tray icon for quick access and status indication
2. WHEN the user right-clicks the tray icon, THE tool SHALL show a context menu with options: Start, Stop, Settings, Exit
3. THE tool SHALL provide a settings window to configure: target window name, check interval, scroll count, click delay
4. THE tool SHALL save configuration to a local file and load it on startup
5. THE tool SHALL display a notification when thanks buttons are clicked

### Requirement 8: 日志与错误处理

**User Story:** As a user, I want the tool to log its activities and handle errors gracefully, so that I can troubleshoot issues.

#### Acceptance Criteria

1. THE tool SHALL log all scan cycles, clicks performed, and errors to a log file
2. WHEN an error occurs during scanning or clicking, THE tool SHALL log the error and continue with the next scheduled cycle
3. THE tool SHALL rotate log files to prevent excessive disk usage
4. IF the target window becomes unresponsive, THEN THE tool SHALL timeout and retry in the next cycle
