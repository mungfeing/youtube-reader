"""
Gemini AI 处理模块
使用 Gemini API 清洗字幕并生成摘要
"""

import os
from typing import Optional, Dict, Any

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("警告: google-generativeai 未安装，Gemini 功能将不可用")


class GeminiProcessor:
    """Gemini 字幕处理器"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化处理器

        Args:
            api_key: Gemini API 密钥，如果为 None 则从环境变量读取
        """
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY')

        if not self.api_key:
            raise ValueError("需要提供 GEMINI_API_KEY")

        if GEMINI_AVAILABLE:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    def process_subtitle(self, subtitle_text: str, video_title: str = "") -> Dict[str, str]:
        """
        处理字幕文本，生成清洗后的文稿和摘要

        Args:
            subtitle_text: 原始字幕文本
            video_title: 视频标题（用于提供上下文）

        Returns:
            包含 'transcript' 和 'summary' 的字典
        """
        if not self.model:
            return {
                'transcript': subtitle_text,
                'summary': "（Gemini 不可用，无法生成摘要）"
            }

        # 如果字幕太长，截取前面的部分
        max_chars = 100000  # Gemini 的上下文限制
        if len(subtitle_text) > max_chars:
            subtitle_text = subtitle_text[:max_chars] + "\n\n[字幕内容过长，已截断...]"

        # 生成清洗后的文稿
        transcript = self._generate_transcript(subtitle_text, video_title)

        # 生成摘要
        summary = self._generate_summary(subtitle_text, video_title)

        return {
            'transcript': transcript,
            'summary': summary
        }

    def _generate_transcript(self, subtitle_text: str, video_title: str) -> str:
        """生成清洗后的完整文稿"""
        prompt = f"""你是一个专业的文字编辑。请将以下视频字幕整理成流畅易读的文章。

要求：
1. 保留完整的内容，不要遗漏重要信息
2. 修正语法错误和口语化表达
3. 添加适当的段落分隔，使文章结构清晰
4. 移除重复的内容、语气词（嗯、啊、那个等）
5. 保持原有的语言风格和专业术语
6. 如果有多个说话者，可以用"主持人："和"嘉宾："等标记区分

视频标题：{video_title}

原始字幕：
{subtitle_text}

请输出整理后的文章："""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"生成文稿失败: {e}")
            return subtitle_text

    def _generate_summary(self, subtitle_text: str, video_title: str) -> str:
        """生成要点摘要"""
        prompt = f"""你是一个专业的内容分析师。请为以下视频内容生成一份要点摘要。

要求：
1. 提取 5-10 个最重要的核心观点
2. 每个要点用 1-2 句话简洁表达
3. 按重要性或逻辑顺序排列
4. 使用 Markdown 列表格式（- 开头）
5. 确保摘要能让读者快速了解视频的核心内容

视频标题：{video_title}

视频字幕内容：
{subtitle_text[:30000]}

请输出要点摘要："""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"生成摘要失败: {e}")
            return "- 摘要生成失败，请查看完整文稿"


def process_video_subtitle(subtitle_text: str, video_title: str = "",
                           api_key: Optional[str] = None) -> Dict[str, str]:
    """
    便捷函数：处理视频字幕

    Args:
        subtitle_text: 原始字幕文本
        video_title: 视频标题
        api_key: Gemini API 密钥

    Returns:
        包含 'transcript' 和 'summary' 的字典
    """
    try:
        processor = GeminiProcessor(api_key)
        return processor.process_subtitle(subtitle_text, video_title)
    except ValueError as e:
        print(f"Gemini 处理器初始化失败: {e}")
        return {
            'transcript': subtitle_text,
            'summary': "- API 密钥未配置，无法生成摘要"
        }


if __name__ == "__main__":
    # 测试代码
    test_subtitle = """
    大家好欢迎来到我的频道
    今天我们要聊一聊人工智能
    嗯这个话题最近非常火
    那个我觉得AI会改变很多行业
    比如说医疗啊教育啊还有交通
    嗯对就是这样
    好的我们下期再见
    """

    if os.environ.get('GEMINI_API_KEY'):
        result = process_video_subtitle(test_subtitle, "AI 的未来发展")
        print("=== 摘要 ===")
        print(result['summary'])
        print("\n=== 文稿 ===")
        print(result['transcript'])
    else:
        print("请设置 GEMINI_API_KEY 环境变量后再测试")
