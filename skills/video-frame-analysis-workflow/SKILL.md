---
name: video-frame-analysis-workflow
description: 当无法直接通过视频工具解析内容时，自动使用 ffmpeg 提取关键帧，并调用图像识别工具对多张帧进行描述，最后由 LLM 整合为完整的视频内容总结。
version: 1.0
evolved_from: none
evolution_type: CAPTURED
---

# video-frame-analysis-workflow

## 适用场景
- 视频文件过大或格式特殊，导致原生视频解析工具（如 `video_parse`）失败。
- 需要对视频中的特定视觉细节（如文字、UI 元素、特定动作）进行高精度分析。
- 视频工具返回的结果过于笼统，需要通过抽帧获取更细致的时间轴描述。

## 步骤
1. **元数据探测**：使用 `ffprobe` 获取视频时长，确定抽帧频率。
2. **创建工作目录**：创建一个临时文件夹（如 `frames/`）存放提取的图片。
3. **执行抽帧**：根据视频长度，使用 `ffmpeg` 提取关键帧。通常建议每 5-10 秒提取一帧，或总数控制在 10-20 张以内。
4. **视觉分析**：循环调用 `image` 工具或具备 Vision 能力的模型，对每一张（或一组）图片进行详细描述。
5. **内容整合**：将所有图片的描述按时间顺序排列，由 LLM 结合上下文逻辑，输出完整的视频内容总结。
6. **清理**：任务完成后删除临时图片文件。

## 工具和命令
### 1. 获取视频时长
```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 input.mp4
```

### 2. 均匀抽帧 (例如每 10 秒截取一帧)
```bash
ffmpeg -i input.mp4 -vf "fps=1/10" frames/out_%03d.jpg
```

### 3. 提取特定数量的帧 (例如总共提取 10 张)
```bash
ffmpeg -i input.mp4 -vf "thumbnail,select='not(mod(n,10))'" -frames:v 10 frames/out_%03d.jpg
```

## 注意事项
- **存储空间**：大量抽帧会迅速消耗磁盘空间，务必根据视频长度调整 `fps` 参数。
- **并发限制**：在调用视觉工具分析多张图片时，注意 API 的并发限制或 Token 消耗。
- **关键信息丢失**：如果视频节奏极快（如快剪视频），较低的抽帧频率可能会漏掉核心画面，需根据视频类型动态调整。
- **清理义务**：必须在 `exec` 步骤最后或任务结束前执行 `rm -rf frames/`，防止环境污染。

## 示例
**任务**：分析一个 60 秒的教学视频。
1. **执行**：`ffmpeg -i tutorial.mp4 -vf "fps=1/5" frames/f_%02d.jpg` (得到 12 张图)。
2. **分析**：逐一识别 `f_01.jpg` (显示标题界面), `f_05.jpg` (展示代码编辑器), `f_10.jpg` (运行结果)。
3. **总结**：该视频是一个关于 Python 基础的教程，前 20 秒介绍概念，中间 30 秒演示代码编写，最后 10 秒展示运行输出。