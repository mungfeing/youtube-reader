"""
视频信息获取模块
使用 yt-dlp 获取 YouTube 频道的视频列表和元数据
"""

import yt_dlp
from typing import List, Dict, Any, Optional
from datetime import datetime


def get_channel_videos(channel_url: str, max_videos: int = 10, min_duration: int = 60) -> List[Dict[str, Any]]:
    """
    获取频道的最新视频列表（过滤掉 Shorts）

    Args:
        channel_url: YouTube 频道 URL
        max_videos: 获取的最大视频数量
        min_duration: 最小时长（秒），低于此时长的视频会被过滤（用于排除Shorts）

    Returns:
        视频信息列表
    """
    # 多获取一些，因为要过滤掉 Shorts
    fetch_count = max_videos * 5

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': 'in_playlist',
        'playlistend': fetch_count,
    }

    videos = []

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 只获取 /videos 页面，不获取 /shorts
            playlist_url = f"{channel_url}/videos"
            result = ydl.extract_info(playlist_url, download=False)

            if result and 'entries' in result:
                for entry in result['entries']:
                    if not entry:
                        continue

                    video_id = entry.get('id')
                    duration = entry.get('duration', 0)

                    # 过滤 Shorts：时长小于60秒的视频
                    if duration and duration < min_duration:
                        continue

                    videos.append({
                        'id': video_id,
                        'title': entry.get('title'),
                        'url': f"https://www.youtube.com/watch?v={video_id}",
                        'duration': duration,
                    })

                    # 达到需要的数量就停止
                    if len(videos) >= max_videos:
                        break

    except Exception as e:
        print(f"获取频道视频列表失败: {e}")

    return videos


def get_video_metadata(video_id: str) -> Optional[Dict[str, Any]]:
    """
    获取单个视频的详细元数据

    Args:
        video_id: YouTube 视频 ID

    Returns:
        视频元数据字典
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            url = f"https://www.youtube.com/watch?v={video_id}"
            info = ydl.extract_info(url, download=False)

            if info:
                # 格式化时长
                duration_seconds = info.get('duration', 0)
                hours, remainder = divmod(duration_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                if hours > 0:
                    duration_str = f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"
                else:
                    duration_str = f"{int(minutes)}:{int(seconds):02d}"

                # 解析上传日期
                upload_date = info.get('upload_date', '')
                if upload_date:
                    try:
                        date_obj = datetime.strptime(upload_date, '%Y%m%d')
                        upload_date_formatted = date_obj.strftime('%Y-%m-%d')
                    except:
                        upload_date_formatted = upload_date
                else:
                    upload_date_formatted = ''

                return {
                    'id': info.get('id'),
                    'title': info.get('title'),
                    'description': info.get('description', ''),
                    'channel': info.get('channel', info.get('uploader', '')),
                    'channel_url': info.get('channel_url', info.get('uploader_url', '')),
                    'upload_date': upload_date_formatted,
                    'duration': duration_str,
                    'duration_seconds': duration_seconds,
                    'view_count': info.get('view_count', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'url': f"https://www.youtube.com/watch?v={info.get('id')}",
                }
    except Exception as e:
        print(f"获取视频元数据失败 [{video_id}]: {e}")

    return None


if __name__ == "__main__":
    # 测试代码
    test_channel = "https://www.youtube.com/@lexfridman"
    print(f"获取频道视频: {test_channel}")
    videos = get_channel_videos(test_channel, max_videos=3)
    print(f"找到 {len(videos)} 个视频")

    if videos:
        print(f"\n获取第一个视频的详细信息...")
        metadata = get_video_metadata(videos[0]['id'])
        if metadata:
            print(f"标题: {metadata['title']}")
            print(f"频道: {metadata['channel']}")
            print(f"时长: {metadata['duration']}")
