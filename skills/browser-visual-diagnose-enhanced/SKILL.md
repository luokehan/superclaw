Hello! I'm ready to help you evolve your browser automation skills. I've prepared the enhanced visual diagnostic skill based on your requirements—what would you like to work on next?

---
name: browser-visual-diagnose-enhanced
description: 自动化处理浏览器操作失败（超时或元素未找到）时的视觉诊断与自动修复流程。
version: 1.1
evolved_from: browser-visual-diagnose
evolution_type: DERIVED
---

# Browser Visual Diagnose Enhanced

## 适用场景
当 `browser` 工具在执行点击、输入或等待元素操作时返回 `TimeoutError`、`ElementNotFound` 或 `Node is detached from document` 等错误时，自动触发此增强诊断流程。特别适用于：
- 动态出现的全局遮罩层（如 Cookie 同意、订阅弹窗）。
- 触发了反爬虫验证界面（如 Cloudflare 等待页、CAPTCHA）。
- 页面布局发生重大偏移导致 CSS 选择器失效。
- 登录 Session 过期导致页面自动跳转至登录墙。

## 步骤
1. **自动捕获异常**：在执行浏览器操作的逻辑中包裹 `try-catch`，一旦捕获到超时或元素缺失异常，立即启动诊断。
2. **视觉采样**：调用 `browser({action: "screenshot"})` 获取当前视口的完整截图。
3. **多模态深度诊断**：将截图输入给视觉模型，并使用以下增强 Prompt：
   > "当前自动化脚本操作失败。请分析截图并识别：
   > 1. 是否存在阻碍交互的弹窗（如 'X' 关闭按钮、'Accept' 按钮）？
   > 2. 是否进入了验证码页面（CAPTCHA）或 Cloudflare 5秒盾验证页？
   > 3. 是否跳转到了登录页面（Login Wall）？
   > 4. 目标区域是否被半透明遮罩覆盖？
   > 请给出阻碍物的中心坐标 (x, y) 及类型标签。"
4. **分类执行修复**：
   - **弹窗类**：识别关闭按钮坐标，执行 `browser({action: "click", x, y})`，等待 500ms 后重试原操作。
   - **验证码/反爬类**：识别为 `WAF_BLOCK` 或 `CAPTCHA`，停止重试，记录拦截类型并向用户报告，请求人工干预或更换代理策略。
   - **登录墙**：识别为 `LOGIN_REQUIRED`，触发 Session 更新流程或提示用户登录。
   - **布局偏移**：若视觉可见但选择器失效，尝试直接根据视觉模型提供的坐标执行 `click`。
5. **状态验证**：修复操作后，再次检查目标元素是否存在。若连续 2 次诊断失败，则彻底报错并输出诊断日志。

## 工具和命令
- `browser({action: "screenshot"})`: 获取现场第一手图像证据。
- `browser({action: "click", x: number, y: number})`: 绕过 DOM 树，直接进行基于坐标的物理点击。
- `browser({action: "evaluate", script: "window.devicePixelRatio"})`: 获取设备像素比，用于校准视觉坐标与点击坐标的映射。

## 注意事项
- **动画缓冲**：弹窗通常伴随淡入动画，建议在捕获异常后延迟 500ms-1000ms 再进行截图，以获取完全显色的 UI 元素。
- **坐标缩放**：视觉模型返回的坐标通常是基于图片像素的，必须结合 `devicePixelRatio` 转换为浏览器的逻辑坐标，否则点击会偏移。
- **死循环预防**：针对同一位置的视觉修复尝试不得超过 2 次，防止在无法关闭的顽固弹窗上陷入死循环。

## 示例
**场景**：脚本尝试在某新闻网站点击“阅读全文”，但报错 `TimeoutError: waiting for selector ".read-more" failed`。
1. **自动触发**：捕获超时错误，执行 `browser({action: "screenshot"})`。
2. **视觉诊断**：模型反馈：“检测到全屏订阅弹窗，关闭按钮位于 (920, 150)”。
3. **执行修复**：
   - 计算逻辑坐标：`x = 920 / pixelRatio`, `y = 150 / pixelRatio`。
   - 执行 `browser({action: "click", x: 920, y: 150})`。
4. **结果**：弹窗消失，脚本自动重试点击“阅读全文”成功。