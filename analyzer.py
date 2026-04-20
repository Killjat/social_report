import os
from typing import Dict, Any, Optional, List
from google import genai
from config import GEMINI_API_KEY
import asyncio


class VideoAnalyzer:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    async def analyze_video(self, video_url: str, prompt: str = None) -> Dict[str, Any]:
        if not prompt:
            prompt = """请分析这个跨境电商相关视频的内容，提取以下信息：
1. 视频主题和产品类型
2. 目标受众和地域
3. 营销策略和亮点
4. 关键数据和统计
5. 总结视频的核心价值和信息"""

        try:
            video_file = self.client.files.upload(file=video_url)
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, video_file]
            )

            return {
                "video_url": video_url,
                "analysis": response.text,
                "status": "success"
            }
        except Exception as e:
            print(f"Error analyzing video {video_url}: {e}")
            return {
                "video_url": video_url,
                "analysis": None,
                "status": "error",
                "error": str(e)
            }

    async def analyze_video_batch(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        tasks = []
        for video in videos:
            if video.get("video_url"):
                tasks.append(self.analyze_video(video["video_url"]))
            elif video.get("url") and video.get("is_video"):
                tasks.append(self.analyze_video(video["url"]))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        analyzed = []
        for i, result in enumerate(results):
            if isinstance(result, dict):
                video_data = videos[i].copy()
                video_data["analysis"] = result.get("analysis", "")
                video_data["analysis_status"] = result.get("status", "error")
                analyzed.append(video_data)
            else:
                video_data = videos[i].copy()
                video_data["analysis"] = None
                video_data["analysis_status"] = "error"
                analyzed.append(video_data)

        return analyzed