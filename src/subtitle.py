"""
字幕下载与解析模块
使用 youtube-transcript-api 获取视频字幕
"""

from typing import Optional, List

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    TRANSCRIPT_API_AVAILABLE = True
except ImportError:
    TRANSCRIPT_API_AVAILABLE = False
    print("警告: youtube-transcript-api 未安装")


def download_subtitle(video_id: str, languages: List[str] = None, use_auto: bool = True) -> Optional[str]:
    """
    下载视频字幕并返回纯文本

    Args:
        video_id: YouTube 视频 ID
        languages: 字幕语言优先级列表
        use_auto: 是否使用自动生成的字幕

    Returns:
        字幕纯文本内容，如果没有字幕则返回 None
    """
    if not TRANSCRIPT_API_AVAILABLE:
        print("youtube-transcript-api 未安装，无法获取字幕")
        return None

    if languages is None:
        languages = ['zh-Hans', 'zh-Hant', 'zh', 'en']

    try:
        api = YouTubeTranscriptApi()

        # 直接获取字幕
        transcript_data = api.fetch(video_id)

        if transcript_data is None or len(transcript_data) == 0:
            print(f"未找到字幕 [{video_id}]")
            return None

        # 提取纯文本
        text_lines = []
        for entry in transcript_data:
            text = entry.text.strip() if hasattr(entry, 'text') else str(entry).strip()
            if text:
                # 清理特殊字符
                text = text.replace('\n', ' ')
                text = text.replace('[音乐]', '')
                text = text.replace('[Music]', '')
                text = text.replace('[Applause]', '')
                text = text.replace('[掌声]', '')
                text = text.replace('[♪♪♪]', '')
                text = ' '.join(text.split())
                if text and not text.startswith('['):
                    text_lines.append(text)

        # 合并文本
        full_text = '\n'.join(text_lines)

        return full_text if full_text else None

    except Exception as e:
        print(f"下载字幕失败 [{video_id}]: {e}")

    return None


if __name__ == "__main__":
    # 测试代码
    test_video_id = "D4wrREvxdBU"  # Peter Yang 的视频
    print(f"下载字幕: {test_video_id}")
    subtitle = download_subtitle(test_video_id, languages=['en'])
    if subtitle:
        print(f"字幕长度: {len(subtitle)} 字符")
        print(f"前500字符:\n{subtitle[:500]}")
    else:
        print("未找到字幕")
