"""
字幕下载与解析模块
使用 yt-dlp 下载视频字幕并解析为纯文本
支持 cookies 认证绕过反爬虫
"""

import os
import re
import tempfile
import yt_dlp
from typing import Optional, List

# cookies 文件路径
COOKIES_FILE = os.environ.get('YOUTUBE_COOKIES_FILE', 'cookies.txt')


def get_ydl_opts(base_opts: dict = None) -> dict:
    """获取 yt-dlp 配置，包含 cookies 支持"""
    opts = {
        'quiet': True,
        'no_warnings': True,
    }

    if base_opts:
        opts.update(base_opts)

    # 如果存在 cookies 文件，使用它
    if os.path.exists(COOKIES_FILE):
        opts['cookiefile'] = COOKIES_FILE

    return opts


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
    if languages is None:
        languages = ['zh-Hans', 'zh-Hant', 'zh', 'en']

    # 创建临时目录存放字幕文件
    with tempfile.TemporaryDirectory() as temp_dir:
        ydl_opts = get_ydl_opts({
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': use_auto,
            'subtitleslangs': languages,
            'subtitlesformat': 'vtt',
            'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
        })

        try:
            url = f"https://www.youtube.com/watch?v={video_id}"

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # 查找下载的字幕文件
            subtitle_text = None
            for lang in languages:
                # 尝试多种可能的文件名格式
                patterns = [
                    f"{video_id}.{lang}.vtt",
                    f"{video_id}.{lang.replace('-', '_')}.vtt",
                ]

                for pattern in patterns:
                    subtitle_path = os.path.join(temp_dir, pattern)
                    if os.path.exists(subtitle_path):
                        with open(subtitle_path, 'r', encoding='utf-8') as f:
                            raw_content = f.read()
                        subtitle_text = parse_vtt(raw_content)
                        if subtitle_text:
                            return subtitle_text

            # 如果按语言名找不到，尝试查找任何 .vtt 文件
            for filename in os.listdir(temp_dir):
                if filename.endswith('.vtt'):
                    subtitle_path = os.path.join(temp_dir, filename)
                    with open(subtitle_path, 'r', encoding='utf-8') as f:
                        raw_content = f.read()
                    subtitle_text = parse_vtt(raw_content)
                    if subtitle_text:
                        return subtitle_text

        except Exception as e:
            print(f"下载字幕失败 [{video_id}]: {e}")

    return None


def parse_vtt(vtt_content: str) -> str:
    """
    解析 VTT 字幕文件，提取纯文本

    Args:
        vtt_content: VTT 文件内容

    Returns:
        清理后的纯文本
    """
    lines = vtt_content.split('\n')
    text_lines = []
    seen_lines = set()  # 用于去重

    for line in lines:
        line = line.strip()

        # 跳过 WEBVTT 头部
        if line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
            continue

        # 跳过时间戳行 (格式: 00:00:00.000 --> 00:00:00.000)
        if re.match(r'^\d{2}:\d{2}:\d{2}\.\d{3}\s*-->', line):
            continue

        # 跳过序号行
        if re.match(r'^\d+$', line):
            continue

        # 跳过空行
        if not line:
            continue

        # 移除 VTT 格式标签 <c>, </c>, <00:00:00.000> 等
        line = re.sub(r'<[^>]+>', '', line)

        # 移除 HTML 实体
        line = line.replace('&nbsp;', ' ')
        line = line.replace('&amp;', '&')
        line = line.replace('&lt;', '<')
        line = line.replace('&gt;', '>')

        # 清理多余空格
        line = ' '.join(line.split())

        if line and line not in seen_lines:
            seen_lines.add(line)
            text_lines.append(line)

    # 合并相邻的相似行
    merged_text = merge_similar_lines(text_lines)

    return merged_text


def merge_similar_lines(lines: List[str]) -> str:
    """
    合并相邻的相似行（处理字幕中的渐进式显示）

    Args:
        lines: 文本行列表

    Returns:
        合并后的文本
    """
    if not lines:
        return ""

    result = []
    prev_line = ""

    for line in lines:
        # 如果当前行是前一行的延续（前一行是当前行的前缀），则替换
        if prev_line and line.startswith(prev_line):
            if result:
                result[-1] = line
        # 如果前一行是当前行的前缀，跳过前一行
        elif line and prev_line.startswith(line):
            pass  # 保留更长的前一行
        else:
            if line:
                result.append(line)

        prev_line = line

    return '\n'.join(result)


if __name__ == "__main__":
    # 测试代码
    test_video_id = "dQw4w9WgXcQ"  # 示例视频
    print(f"下载字幕: {test_video_id}")
    subtitle = download_subtitle(test_video_id, languages=['en'])
    if subtitle:
        print(f"字幕长度: {len(subtitle)} 字符")
        print(f"前500字符:\n{subtitle[:500]}")
    else:
        print("未找到字幕")
