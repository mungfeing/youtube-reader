"""
RSS 生成模块
生成标准 RSS 2.0 格式的订阅源
"""

import os
from typing import List, Dict, Any
from datetime import datetime
from feedgen.feed import FeedGenerator


def generate_rss(videos: List[Dict[str, Any]],
                 output_path: str,
                 feed_title: str = "YouTube 播客阅读器",
                 feed_description: str = "自动整理的 YouTube 播客内容",
                 feed_link: str = "https://example.com",
                 max_items: int = 50):
    """
    生成 RSS 订阅源

    Args:
        videos: 视频信息列表
        output_path: 输出文件路径
        feed_title: RSS 源标题
        feed_description: RSS 源描述
        feed_link: RSS 源链接
        max_items: 最大条目数
    """
    fg = FeedGenerator()
    fg.title(feed_title)
    fg.description(feed_description)
    fg.link(href=feed_link, rel='alternate')
    fg.language('zh-CN')
    fg.lastBuildDate(datetime.now())

    # 按日期排序
    sorted_videos = sorted(videos,
                           key=lambda x: x.get('upload_date', ''),
                           reverse=True)

    for video in sorted_videos[:max_items]:
        fe = fg.add_entry()

        video_id = video.get('id', '')
        title = video.get('title', '未知标题')
        url = video.get('url', f'https://youtube.com/watch?v={video_id}')
        channel = video.get('channel', '')
        upload_date = video.get('upload_date', '')
        summary = video.get('summary_preview', video.get('description', ''))

        fe.id(url)
        fe.title(title)
        fe.link(href=url)
        fe.author({'name': channel})

        # 构建描述内容
        description = f"<p><strong>频道</strong>: {channel}</p>"
        if summary:
            description += f"<p><strong>摘要</strong>:</p><p>{summary}</p>"
        description += f'<p><a href="{url}">观看原视频</a></p>'
        fe.description(description)

        # 设置发布日期
        if upload_date:
            try:
                pub_date = datetime.strptime(upload_date, '%Y-%m-%d')
                fe.pubDate(pub_date)
            except ValueError:
                pass

    # 确保目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 保存 RSS 文件
    fg.rss_file(output_path)
    print(f"RSS 文件已生成: {output_path}")


def update_rss(new_videos: List[Dict[str, Any]],
               existing_videos: List[Dict[str, Any]],
               output_path: str,
               **kwargs):
    """
    更新 RSS 源，添加新视频

    Args:
        new_videos: 新视频列表
        existing_videos: 现有视频列表
        output_path: 输出文件路径
        **kwargs: 其他参数传递给 generate_rss
    """
    # 合并视频列表，新视频在前
    all_videos = new_videos + existing_videos

    # 去重
    seen_ids = set()
    unique_videos = []
    for video in all_videos:
        vid = video.get('id')
        if vid and vid not in seen_ids:
            seen_ids.add(vid)
            unique_videos.append(video)

    generate_rss(unique_videos, output_path, **kwargs)


if __name__ == "__main__":
    # 测试代码
    test_videos = [
        {
            'id': 'video1',
            'title': '测试视频 1',
            'url': 'https://youtube.com/watch?v=video1',
            'channel': '测试频道',
            'upload_date': '2025-01-10',
            'summary_preview': '这是视频1的摘要内容'
        },
        {
            'id': 'video2',
            'title': '测试视频 2',
            'url': 'https://youtube.com/watch?v=video2',
            'channel': '另一个频道',
            'upload_date': '2025-01-09',
            'summary_preview': '这是视频2的摘要内容'
        }
    ]

    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as f:
        test_output = f.name

    generate_rss(test_videos, test_output)

    # 读取并显示生成的内容
    with open(test_output, 'r', encoding='utf-8') as f:
        print(f.read()[:1000])

    os.unlink(test_output)
