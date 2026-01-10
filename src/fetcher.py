"""
视频信息获取模块
使用 YouTube RSS Feed 获取频道视频列表，避免反爬虫限制
"""

import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError
import json


def get_channel_id(channel_url: str) -> Optional[str]:
    """
    从频道 URL 获取 channel_id

    Args:
        channel_url: YouTube 频道 URL (支持 @handle 格式)

    Returns:
        channel_id 或 None
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        req = Request(channel_url, headers=headers)
        with urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')

        # 从页面中提取 channel_id
        patterns = [
            r'"channelId":"([^"]+)"',
            r'channel_id=([^"&]+)',
            r'"externalId":"([^"]+)"',
        ]

        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)

    except Exception as e:
        print(f"获取 channel_id 失败: {e}")

    return None


def get_channel_videos(channel_url: str, max_videos: int = 10, min_duration: int = 60) -> List[Dict[str, Any]]:
    """
    获取频道的最新视频列表

    Args:
        channel_url: YouTube 频道 URL
        max_videos: 获取的最大视频数量
        min_duration: 最小时长（秒），低于此时长的视频会被过滤（用于排除Shorts）

    Returns:
        视频信息列表
    """
    # 获取 channel_id
    channel_id = get_channel_id(channel_url)
    if not channel_id:
        print(f"无法获取频道 ID: {channel_url}")
        return []

    # 使用 RSS Feed 获取视频列表
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    videos = []

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        req = Request(rss_url, headers=headers)
        with urlopen(req, timeout=30) as response:
            xml_content = response.read()

        # 解析 XML
        root = ET.fromstring(xml_content)

        # 定义命名空间
        namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'yt': 'http://www.youtube.com/xml/schemas/2015',
            'media': 'http://search.yahoo.com/mrss/'
        }

        # 获取所有 entry
        entries = root.findall('atom:entry', namespaces)

        for entry in entries[:max_videos * 2]:  # 多获取一些以备过滤
            video_id = entry.find('yt:videoId', namespaces)
            title = entry.find('atom:title', namespaces)
            published = entry.find('atom:published', namespaces)

            if video_id is not None and title is not None:
                videos.append({
                    'id': video_id.text,
                    'title': title.text,
                    'url': f"https://www.youtube.com/watch?v={video_id.text}",
                    'published': published.text if published is not None else '',
                })

            if len(videos) >= max_videos:
                break

    except Exception as e:
        print(f"获取频道视频列表失败: {e}")

    return videos


def get_video_metadata(video_id: str) -> Optional[Dict[str, Any]]:
    """
    获取单个视频的详细元数据（使用 oembed API）

    Args:
        video_id: YouTube 视频 ID

    Returns:
        视频元数据字典
    """
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    oembed_url = f"https://www.youtube.com/oembed?url={video_url}&format=json"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        req = Request(oembed_url, headers=headers)
        with urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))

        # 从视频页面获取更多信息
        req = Request(video_url, headers=headers)
        with urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')

        # 提取上传日期
        upload_date = ''
        date_match = re.search(r'"uploadDate":"([^"]+)"', html)
        if date_match:
            try:
                date_str = date_match.group(1)
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                upload_date = date_obj.strftime('%Y-%m-%d')
            except:
                pass

        # 提取时长
        duration_str = ''
        duration_seconds = 0
        duration_match = re.search(r'"lengthSeconds":"(\d+)"', html)
        if duration_match:
            duration_seconds = int(duration_match.group(1))
            hours, remainder = divmod(duration_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours > 0:
                duration_str = f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"
            else:
                duration_str = f"{int(minutes)}:{int(seconds):02d}"

        # 提取观看次数
        view_count = 0
        view_match = re.search(r'"viewCount":"(\d+)"', html)
        if view_match:
            view_count = int(view_match.group(1))

        # 提取描述
        description = ''
        desc_match = re.search(r'"shortDescription":"([^"]*)"', html)
        if desc_match:
            description = desc_match.group(1).encode().decode('unicode_escape')

        return {
            'id': video_id,
            'title': data.get('title', ''),
            'description': description,
            'channel': data.get('author_name', ''),
            'channel_url': data.get('author_url', ''),
            'upload_date': upload_date,
            'duration': duration_str,
            'duration_seconds': duration_seconds,
            'view_count': view_count,
            'thumbnail': data.get('thumbnail_url', ''),
            'url': video_url,
        }

    except Exception as e:
        print(f"获取视频元数据失败 [{video_id}]: {e}")

    return None


if __name__ == "__main__":
    # 测试代码
    test_channel = "https://www.youtube.com/@PeterYangYT"
    print(f"获取频道视频: {test_channel}")
    videos = get_channel_videos(test_channel, max_videos=3)
    print(f"找到 {len(videos)} 个视频")

    for v in videos:
        print(f"  - {v['title']}")

    if videos:
        print(f"\n获取第一个视频的详细信息...")
        metadata = get_video_metadata(videos[0]['id'])
        if metadata:
            print(f"标题: {metadata['title']}")
            print(f"频道: {metadata['channel']}")
            print(f"时长: {metadata['duration']}")
            print(f"上传日期: {metadata['upload_date']}")
