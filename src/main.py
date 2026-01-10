#!/usr/bin/env python3
"""
YouTube 播客阅读器 - 主入口
自动获取指定频道的新视频，下载字幕，使用 Gemini 清洗，生成 Markdown 文档
"""

import os
import sys
import json
import yaml
from datetime import datetime
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetcher import get_channel_videos, get_video_metadata
from subtitle import download_subtitle
from gemini_processor import process_video_subtitle
from dedup import VideoDeduplicator
from formatter import format_video_document, format_daily_summary, format_index, save_document
from rss_generator import generate_rss


def load_config(config_path: str) -> dict:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent


def main():
    """主函数"""
    print("=" * 60)
    print("YouTube 播客阅读器")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 路径设置
    project_root = get_project_root()
    config_path = project_root / "config" / "channels.yaml"
    data_path = project_root / "data" / "videos.json"
    output_dir = project_root / "output"
    docs_dir = output_dir / "docs"
    videos_dir = docs_dir / "videos"
    rss_path = output_dir / "feed.xml"

    # 确保目录存在
    videos_dir.mkdir(parents=True, exist_ok=True)

    # 加载配置
    print("\n[1/6] 加载配置...")
    config = load_config(config_path)
    channels = config.get('channels', [])
    settings = config.get('settings', {})

    max_videos = settings.get('max_videos_per_channel', 10)
    subtitle_languages = settings.get('subtitle_languages', ['zh-Hans', 'zh', 'en'])
    use_auto_subtitles = settings.get('use_auto_subtitles', True)

    print(f"    发现 {len(channels)} 个订阅频道")

    # 初始化去重器
    print("\n[2/6] 初始化去重器...")
    dedup = VideoDeduplicator(str(data_path))
    print(f"    已处理视频数: {dedup.get_processed_count()}")

    # 获取所有频道的视频
    print("\n[3/6] 获取频道视频列表...")
    all_new_videos = []

    for channel in channels:
        channel_name = channel.get('name', '未知频道')
        channel_url = channel.get('url', '')
        category = channel.get('category', '')

        if not channel_url:
            print(f"    跳过无效频道: {channel_name}")
            continue

        print(f"    获取: {channel_name}")
        videos = get_channel_videos(channel_url, max_videos)
        print(f"        找到 {len(videos)} 个视频")

        # 过滤新视频
        new_videos = dedup.filter_new_videos(videos)
        print(f"        新视频: {len(new_videos)} 个")

        # 添加频道信息
        for video in new_videos:
            video['channel_name'] = channel_name
            video['category'] = category

        all_new_videos.extend(new_videos)

    if not all_new_videos:
        print("\n没有新视频需要处理")
        return

    print(f"\n共发现 {len(all_new_videos)} 个新视频")

    # 处理每个新视频
    print("\n[4/6] 处理视频...")
    processed_videos = []

    for i, video in enumerate(all_new_videos, 1):
        video_id = video.get('id')
        title = video.get('title', '未知')
        print(f"\n    [{i}/{len(all_new_videos)}] {title[:50]}...")

        # 获取详细元数据
        print("        获取元数据...")
        metadata = get_video_metadata(video_id)
        if not metadata:
            print("        失败: 无法获取元数据")
            continue

        # 合并频道信息
        metadata['channel'] = video.get('channel_name', metadata.get('channel', ''))
        metadata['category'] = video.get('category', '')

        # 下载字幕
        print("        下载字幕...")
        subtitle = download_subtitle(video_id, subtitle_languages, use_auto_subtitles)

        if not subtitle:
            print("        警告: 未找到字幕，跳过此视频")
            continue

        print(f"        字幕长度: {len(subtitle)} 字符")

        # 使用 Gemini 处理字幕
        print("        AI 处理中...")
        try:
            result = process_video_subtitle(subtitle, metadata.get('title', ''))
            transcript = result.get('transcript', subtitle)
            summary = result.get('summary', '')
        except Exception as e:
            print(f"        AI 处理失败: {e}")
            transcript = subtitle
            summary = "- 摘要生成失败"

        # 生成 Markdown 文档
        print("        生成文档...")
        doc_content = format_video_document(metadata, transcript, summary)
        doc_path = videos_dir / f"{video_id}.md"
        save_document(doc_content, str(doc_path))

        # 提取摘要预览（前3个要点）
        summary_lines = [line for line in summary.split('\n') if line.strip().startswith('-')]
        summary_preview = '\n'.join(summary_lines[:3]) if summary_lines else ''

        # 记录处理结果
        processed_video = {
            **metadata,
            'summary_preview': summary_preview,
            'processed_at': datetime.now().isoformat()
        }
        processed_videos.append(processed_video)

        # 标记为已处理
        dedup.mark_processed(video_id)
        print("        完成")

    # 生成每日汇总
    print("\n[5/6] 生成汇总文档...")
    if processed_videos:
        today = datetime.now().strftime('%Y-%m-%d')
        daily_doc = format_daily_summary(processed_videos, today)
        save_document(daily_doc, str(docs_dir / f"{today}.md"))
        print(f"    每日汇总: {today}.md")

    # 加载所有已处理视频的信息用于索引
    all_processed = []
    for video_file in videos_dir.glob("*.md"):
        video_id = video_file.stem
        # 尝试从处理结果中获取信息
        for v in processed_videos:
            if v.get('id') == video_id:
                all_processed.append(v)
                break

    # 生成索引
    index_doc = format_index(all_processed if all_processed else processed_videos)
    save_document(index_doc, str(docs_dir / "index.md"))
    print("    索引: index.md")

    # 生成 RSS
    print("\n[6/6] 生成 RSS 订阅源...")
    generate_rss(processed_videos, str(rss_path))

    # 完成
    print("\n" + "=" * 60)
    print("处理完成!")
    print(f"- 处理视频数: {len(processed_videos)}")
    print(f"- 文档目录: {docs_dir}")
    print(f"- RSS 文件: {rss_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
