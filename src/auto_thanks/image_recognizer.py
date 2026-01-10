"""Image recognition module using OpenCV template matching."""

import os
import logging
from typing import Dict, List, Optional

import cv2
import numpy as np

# Use try/except to handle both relative imports (development) and absolute imports (bundled)
try:
    from .models import MatchResult
except ImportError:
    from auto_thanks.models import MatchResult

logger = logging.getLogger(__name__)


class TemplateDirectoryError(Exception):
    """Exception raised when the templates directory is missing or invalid.
    
    This exception is raised during startup if the templates directory
    does not exist, prompting the user to prepare the required template images.
    """
    pass


class ImageRecognizer:
    """图像识别模块，使用模板匹配识别UI元素"""

    # Template file names
    TEMPLATE_THANKS = "thanks_button.png"
    TEMPLATE_THANKED = "thanked_button.png"
    TEMPLATE_DIVIDER = "divider_line.png"
    TEMPLATE_TAB_LIKES = "tab_likes.png"
    TEMPLATE_TAB_FOLLOWS = "tab_follows.png"
    TEMPLATE_TAB_INDICATOR = "tab_indicator.png"
    
    # Required templates that must exist for the app to function
    # - thanks_button.png and thanked_button.png: Core button recognition (Requirements 3.1, 3.4)
    # - tab_likes.png and tab_follows.png: Tab switching functionality (Requirements 2.1)
    REQUIRED_TEMPLATES = [
        TEMPLATE_THANKS, 
        TEMPLATE_THANKED,
        TEMPLATE_TAB_LIKES,
        TEMPLATE_TAB_FOLLOWS,
    ]
    
    # Optional templates that enhance functionality but are not required:
    # - divider_line.png: Used to filter buttons above the divider line (Requirement 3.2)
    #   If missing, all visible buttons are processed per Requirement 3.5:
    #   "IF no Divider_Line is found, THEN THE Image_Recognizer SHALL process all visible Thanks_Buttons"
    # - tab_indicator.png: Used to detect "+X" indicators for tab prioritization (Requirement 2.2)
    #   If missing, tabs are processed in default order without prioritization
    OPTIONAL_TEMPLATES = [
        TEMPLATE_DIVIDER,
        TEMPLATE_TAB_INDICATOR,
    ]

    def __init__(self, templates_dir: str, confidence_threshold: float = 0.8):
        """
        初始化图像识别器

        Args:
            templates_dir: 模板图片目录路径
            confidence_threshold: 匹配置信度阈值 (0.0-1.0)
        """
        self.templates_dir = templates_dir
        self.confidence_threshold = max(0.0, min(1.0, confidence_threshold))
        self._templates: Dict[str, np.ndarray] = {}

    def load_templates(self) -> Dict[str, np.ndarray]:
        """
        加载所有模板图片

        Returns:
            模板名称到图像数组的映射
            
        Raises:
            TemplateDirectoryError: 如果模板目录不存在
        """
        self._templates = {}

        if not os.path.isdir(self.templates_dir):
            error_msg = (
                f"模板目录不存在: {self.templates_dir}\n\n"
                f"请准备以下模板图片并放入该目录:\n\n"
                f"【必需模板】(缺少任何一个将无法启动):\n"
                f"  - thanks_button.png (谢谢按钮)\n"
                f"  - thanked_button.png (已感谢按钮)\n"
                f"  - tab_likes.png (赞标签)\n"
                f"  - tab_follows.png (关注标签)\n\n"
                f"【可选模板】(缺少时使用降级功能):\n"
                f"  - divider_line.png (分界线) - 缺少时处理所有可见按钮\n"
                f"  - tab_indicator.png (+X指示器) - 缺少时按默认顺序处理标签"
            )
            logger.error(f"Templates directory not found: {self.templates_dir}")
            raise TemplateDirectoryError(error_msg)

        for filename in os.listdir(self.templates_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                filepath = os.path.join(self.templates_dir, filename)
                template = cv2.imread(filepath, cv2.IMREAD_COLOR)
                if template is not None:
                    self._templates[filename] = template
                    logger.debug(f"Loaded template: {filename}")
                else:
                    logger.warning(f"Failed to load template: {filepath}")

        logger.info(f"Loaded {len(self._templates)} templates")
        
        # Verify required templates exist
        missing_templates = []
        for required in self.REQUIRED_TEMPLATES:
            if required not in self._templates:
                missing_templates.append(required)
        
        if missing_templates:
            # List all required templates with descriptions for clarity
            required_list = (
                f"  - {self.TEMPLATE_THANKS} (谢谢按钮) - 必需\n"
                f"  - {self.TEMPLATE_THANKED} (已感谢按钮) - 必需\n"
                f"  - {self.TEMPLATE_TAB_LIKES} (赞标签) - 必需\n"
                f"  - {self.TEMPLATE_TAB_FOLLOWS} (关注标签) - 必需"
            )
            optional_list = (
                f"  - {self.TEMPLATE_DIVIDER} (分界线) - 可选，缺少时处理所有可见按钮\n"
                f"  - {self.TEMPLATE_TAB_INDICATOR} (+X指示器) - 可选，缺少时按默认顺序处理标签"
            )
            error_msg = (
                f"缺少必需的模板文件:\n"
                f"  - " + "\n  - ".join(missing_templates) + "\n\n"
                f"【必需模板】:\n{required_list}\n\n"
                f"【可选模板】:\n{optional_list}\n\n"
                f"请将模板图片放入目录: {self.templates_dir}"
            )
            logger.error(f"Missing required templates: {missing_templates}")
            raise TemplateDirectoryError(error_msg)
        
        # Log info about optional templates
        for optional in self.OPTIONAL_TEMPLATES:
            if optional not in self._templates:
                if optional == self.TEMPLATE_DIVIDER:
                    logger.info(f"Optional template '{optional}' not found - will process all visible buttons")
                elif optional == self.TEMPLATE_TAB_INDICATOR:
                    logger.info(f"Optional template '{optional}' not found - tab prioritization disabled")
        
        return self._templates

    def find_template(
        self, screenshot: np.ndarray, template_name: str
    ) -> List[MatchResult]:
        """
        在截图中查找指定模板

        Args:
            screenshot: 截图图像 (BGR format)
            template_name: 模板名称

        Returns:
            所有匹配结果列表
        """
        results: List[MatchResult] = []

        if screenshot is None or screenshot.size == 0:
            logger.warning("Invalid screenshot provided")
            return results

        # Get template from cache or load it
        template = self._templates.get(template_name)
        if template is None:
            template_path = os.path.join(self.templates_dir, template_name)
            if os.path.exists(template_path):
                template = cv2.imread(template_path, cv2.IMREAD_COLOR)
                if template is not None:
                    self._templates[template_name] = template
            
            if template is None:
                logger.warning(f"Template not found: {template_name}")
                return results

        # Get template dimensions
        h, w = template.shape[:2]

        # Ensure screenshot is large enough for template
        if screenshot.shape[0] < h or screenshot.shape[1] < w:
            logger.debug(f"Screenshot too small for template {template_name}")
            return results

        # Perform template matching
        try:
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        except cv2.error as e:
            logger.error(f"Template matching failed: {e}")
            return results

        # Find all locations above threshold
        locations = np.where(result >= self.confidence_threshold)

        # Group nearby matches to avoid duplicates
        matched_points: List[tuple] = []
        for pt in zip(*locations[::-1]):  # Switch x and y
            # Check if this point is too close to an existing match
            is_duplicate = False
            for existing in matched_points:
                if abs(pt[0] - existing[0]) < w // 2 and abs(pt[1] - existing[1]) < h // 2:
                    is_duplicate = True
                    break

            if not is_duplicate:
                matched_points.append(pt)
                confidence = float(result[pt[1], pt[0]])
                # Calculate center point
                center_x = pt[0] + w // 2
                center_y = pt[1] + h // 2
                results.append(
                    MatchResult(
                        x=center_x,
                        y=center_y,
                        width=w,
                        height=h,
                        confidence=confidence,
                        template_name=template_name,
                    )
                )

        logger.debug(f"Found {len(results)} matches for {template_name}")
        return results


    def find_thanks_buttons(self, screenshot: np.ndarray) -> List[MatchResult]:
        """
        查找所有"谢谢"按钮

        Args:
            screenshot: 截图图像

        Returns:
            谢谢按钮的匹配结果列表
        """
        return self.find_template(screenshot, self.TEMPLATE_THANKS)

    def find_thanked_buttons(self, screenshot: np.ndarray) -> List[MatchResult]:
        """
        查找所有"已感谢"按钮

        Args:
            screenshot: 截图图像

        Returns:
            已感谢按钮的匹配结果列表
        """
        return self.find_template(screenshot, self.TEMPLATE_THANKED)

    def find_divider_line(self, screenshot: np.ndarray) -> Optional[int]:
        """
        查找分界线位置

        Args:
            screenshot: 截图图像

        Returns:
            分界线的 Y 坐标（中心点），未找到返回 None
        """
        matches = self.find_template(screenshot, self.TEMPLATE_DIVIDER)
        if not matches:
            return None

        # Return the Y coordinate of the first (highest confidence) match
        # Sort by confidence descending and return the Y of the best match
        best_match = max(matches, key=lambda m: m.confidence)
        return best_match.y

    def find_tab_buttons(self, screenshot: np.ndarray) -> Dict[str, MatchResult]:
        """
        查找标签页按钮（赞、关注）

        Args:
            screenshot: 截图图像

        Returns:
            标签名称到匹配结果的映射
        """
        result: Dict[str, MatchResult] = {}

        # Find "赞" tab
        likes_matches = self.find_template(screenshot, self.TEMPLATE_TAB_LIKES)
        if likes_matches:
            result["赞"] = max(likes_matches, key=lambda m: m.confidence)

        # Find "关注" tab
        follows_matches = self.find_template(screenshot, self.TEMPLATE_TAB_FOLLOWS)
        if follows_matches:
            result["关注"] = max(follows_matches, key=lambda m: m.confidence)

        return result

    def find_tab_indicators(self, screenshot: np.ndarray) -> List[MatchResult]:
        """
        查找标签页上的"+X"指示器

        Args:
            screenshot: 截图图像

        Returns:
            所有"+X"指示器的匹配结果列表
        """
        return self.find_template(screenshot, self.TEMPLATE_TAB_INDICATOR)

    def get_tabs_with_indicators(
        self, 
        screenshot: np.ndarray
    ) -> Dict[str, bool]:
        """
        检测哪些标签页有"+X"指示器

        Args:
            screenshot: 截图图像

        Returns:
            标签名称到是否有指示器的映射 {"赞": True/False, "关注": True/False}
        """
        result: Dict[str, bool] = {"赞": False, "关注": False}
        
        # Find tab buttons first
        tab_buttons = self.find_tab_buttons(screenshot)
        if not tab_buttons:
            return result
        
        # Find all indicators
        indicators = self.find_tab_indicators(screenshot)
        if not indicators:
            return result
        
        # For each tab, check if there's an indicator nearby (to the right)
        # Indicators typically appear right after the tab text
        indicator_tolerance_x = 100  # pixels to the right of tab
        indicator_tolerance_y = 20   # pixels vertical tolerance
        
        for tab_name, tab_match in tab_buttons.items():
            for indicator in indicators:
                # Check if indicator is to the right of tab and vertically aligned
                x_diff = indicator.x - tab_match.x
                y_diff = abs(indicator.y - tab_match.y)
                
                if 0 < x_diff < indicator_tolerance_x and y_diff < indicator_tolerance_y:
                    result[tab_name] = True
                    logger.debug(f"Found indicator for tab '{tab_name}' at ({indicator.x}, {indicator.y})")
                    break
        
        return result


    def filter_buttons_above_divider(
        self, buttons: List[MatchResult], divider_y: Optional[int]
    ) -> List[MatchResult]:
        """
        过滤出分界线上方的按钮

        Args:
            buttons: 按钮列表
            divider_y: 分界线 Y 坐标

        Returns:
            分界线上方的按钮列表（如果 divider_y 为 None，返回所有按钮）
        """
        if divider_y is None:
            # No divider found, return all buttons (per Requirement 3.5)
            return list(buttons)

        # Filter buttons where Y coordinate is strictly less than divider Y
        filtered = [btn for btn in buttons if btn.y < divider_y]
        logger.debug(
            f"Filtered {len(buttons)} buttons to {len(filtered)} above divider at y={divider_y}"
        )
        return filtered
