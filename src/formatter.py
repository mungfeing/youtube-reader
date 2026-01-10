"""
Markdown 格式化模块
将视频信息和处理后的内容生成 Markdown 文档
"""

import os
from typing import Dict, Any, List
from datetime import datetime


def format_video_document(video_metadata: Dict[str, Any],
                          transcript: str,
                          summary: str) -> str:
    """
    生成单个视频的 Markdown 文档

    Args:
        video_metadata: 视频元数据
        transcript: 清洗后的文稿
        summary: 要点摘要

    Returns:
        Markdown 格式的文档内容
    """
    title = video_metadata.get('title', '未知标题')
    channel = video_metadata.get('channel', '未知频道')
    upload_date = video_metadata.get('upload_date', '未知日期')
    duration = video_metadata.get('duration', '未知')
    url = video_metadata.get('url', '')
    description = video_metadata.get('description', '')

    # 截取描述的前300字符
    if len(description) > 300:
        description = description[:300] + '...'

    doc = f"""# {title}

> **频道**: {channel} | **发布时间**: {upload_date} | **时长**: {duration}

## 要点摘要

{summary}

## 完整文稿

{transcript}

---

## 原始信息

**视频描述**:
{description if description else '无描述'}

**原视频链接**: [{title}]({url})

---
*文档生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    return doc


def format_daily_summary(videos: List[Dict[str, Any]], date: str = None) -> str:
    """
    生成每日更新汇总文档

    Args:
        videos: 视频信息列表
        date: 日期字符串，默认为今天

    Returns:
        Markdown 格式的汇总文档
    """
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')

    doc = f"""# 每日更新 - {date}

> 今日共更新 **{len(videos)}** 个视频

---

"""
    for i, video in enumerate(videos, 1):
        title = video.get('title', '未知标题')
        channel = video.get('channel', '未知频道')
        duration = video.get('duration', '')
        video_id = video.get('id', '')
        summary_preview = video.get('summary_preview', '')

        doc += f"""## {i}. {title}

- **频道**: {channel}
- **时长**: {duration}
- **详情**: [查看完整文档](videos/{video_id}.md)

{summary_preview}

---

"""

    doc += f"""
*更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    return doc


def format_index(all_videos: List[Dict[str, Any]]) -> str:
    """
    生成文档索引页

    Args:
        all_videos: 所有视频的信息列表

    Returns:
        Markdown 格式的索引文档
    """
    doc = """# YouTube 播客阅读器 - 文档索引

## 最近更新

| 日期 | 标题 | 频道 | 时长 |
|------|------|------|------|
"""

    # 按日期排序，最新的在前
    sorted_videos = sorted(all_videos,
                           key=lambda x: x.get('upload_date', ''),
                           reverse=True)

    for video in sorted_videos[:50]:  # 只显示最近50个
        title = video.get('title', '未知')
        channel = video.get('channel', '未知')
        duration = video.get('duration', '')
        upload_date = video.get('upload_date', '')
        video_id = video.get('id', '')

        # 标题太长则截断
        if len(title) > 50:
            title = title[:47] + '...'

        doc += f"| {upload_date} | [{title}](videos/{video_id}.md) | {channel} | {duration} |\n"

    doc += f"""
---

## 统计信息

- **总视频数**: {len(all_videos)}
- **最后更新**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## RSS 订阅

[订阅 RSS](../feed.xml)
"""
    return doc


def save_document(content: str, filepath: str):
    """
    保存文档到文件

    Args:
        content: 文档内容
        filepath: 文件路径
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


if __name__ == "__main__":
    # 测试代码
    test_metadata = {
        'id': 'abc123',
        'title': '测试视频标题',
        'channel': '测试频道',
        'upload_date': '2025-01-10',
        'duration': '1:30:00',
        'url': 'https://youtube.com/watch?v=abc123',
        'description': '这是一个测试视频的描述'
    }

    test_summary = """- 这是第一个要点
- 这是第二个要点
- 这是第三个要点"""

    test_transcript = """这是整理后的文稿内容。

经过 AI 处理，文字变得更加流畅易读。

内容被分成了多个段落。"""

    doc = format_video_document(test_metadata, test_transcript, test_summary)
    print(doc)
