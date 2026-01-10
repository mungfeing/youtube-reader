"""
视频去重模块
管理已处理的视频记录，避免重复处理
"""

import json
import os
from typing import List, Dict, Any, Set
from datetime import datetime


class VideoDeduplicator:
    """视频去重管理器"""

    def __init__(self, data_file: str):
        """
        初始化去重器

        Args:
            data_file: 存储已处理视频的 JSON 文件路径
        """
        self.data_file = data_file
        self.processed_ids: Set[str] = set()
        self._load()

    def _load(self):
        """从文件加载已处理的视频 ID"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.processed_ids = set(data.get('processed_videos', []))
            except (json.JSONDecodeError, IOError) as e:
                print(f"加载去重数据失败: {e}")
                self.processed_ids = set()
        else:
            self.processed_ids = set()

    def _save(self):
        """保存已处理的视频 ID 到文件"""
        # 确保目录存在
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

        data = {
            'processed_videos': list(self.processed_ids),
            'last_updated': datetime.now().isoformat()
        }

        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def is_processed(self, video_id: str) -> bool:
        """
        检查视频是否已处理

        Args:
            video_id: 视频 ID

        Returns:
            是否已处理
        """
        return video_id in self.processed_ids

    def mark_processed(self, video_id: str):
        """
        标记视频为已处理

        Args:
            video_id: 视频 ID
        """
        self.processed_ids.add(video_id)
        self._save()

    def mark_batch_processed(self, video_ids: List[str]):
        """
        批量标记视频为已处理

        Args:
            video_ids: 视频 ID 列表
        """
        self.processed_ids.update(video_ids)
        self._save()

    def filter_new_videos(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        过滤出未处理的新视频

        Args:
            videos: 视频列表，每个视频需要有 'id' 字段

        Returns:
            未处理的视频列表
        """
        return [v for v in videos if v.get('id') and not self.is_processed(v['id'])]

    def get_processed_count(self) -> int:
        """获取已处理的视频数量"""
        return len(self.processed_ids)

    def clear(self):
        """清除所有记录（谨慎使用）"""
        self.processed_ids = set()
        self._save()


if __name__ == "__main__":
    # 测试代码
    import tempfile

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        test_file = f.name

    dedup = VideoDeduplicator(test_file)

    # 测试添加
    dedup.mark_processed("video1")
    dedup.mark_processed("video2")
    print(f"已处理数量: {dedup.get_processed_count()}")

    # 测试检查
    print(f"video1 已处理: {dedup.is_processed('video1')}")
    print(f"video3 已处理: {dedup.is_processed('video3')}")

    # 测试过滤
    test_videos = [
        {'id': 'video1', 'title': '视频1'},
        {'id': 'video2', 'title': '视频2'},
        {'id': 'video3', 'title': '视频3'},
    ]
    new_videos = dedup.filter_new_videos(test_videos)
    print(f"新视频: {[v['title'] for v in new_videos]}")

    # 清理
    os.unlink(test_file)
