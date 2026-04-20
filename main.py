import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from searcher import SocialMediaSearcher
from analyzer import VideoAnalyzer
from keyword_analyzer import KeywordAnalyzer
from config import SEARCH_KEYWORDS, PLATFORMS


class IntelligenceProcessor:
    def __init__(self):
        self.searcher = SocialMediaSearcher()
        self.analyzer = VideoAnalyzer()
        self.keyword_analyzer = KeywordAnalyzer()

    async def gather_intelligence(self) -> List[Dict[str, Any]]:
        raw_data = await self.searcher.search_all()
        return self.process_raw_data(raw_data)

    def process_raw_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        processed = []
        for item in raw_data:
            item["gathered_at"] = datetime.now().isoformat()
            if item.get("is_video"):
                item["needs_analysis"] = True
            processed.append(item)
        return processed

    async def analyze_videos(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        video_items = [item for item in data if item.get("is_video") or item.get("video_url")]
        if not video_items:
            return data
        
        analyzed = await self.analyzer.analyze_video_batch(video_items)
        
        result_map = {item["id"]: item for item in analyzed}
        for item in data:
            if item["id"] in result_map:
                item["analysis"] = result_map[item["id"]].get("analysis")
                item["analysis_status"] = result_map[item["id"]].get("analysis_status", "pending")
        
        return data

    def ai_refine_keywords(self, data: List[Dict[str, Any]], current_keywords: List[str]) -> List[str]:
        print("🤖 AI analyzing content to refine keywords...")
        refined = self.keyword_analyzer.analyze_and_expand(data, current_keywords)
        print(f"📝 Keywords refined: {len(refined)} total")
        return refined

    def ai_extract_insights(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        print("🤖 AI extracting insights...")
        return self.keyword_analyzer.extract_insights(data)

    def enrich_intelligence(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成统计摘要，不嵌套进每条数据"""
        insights = {
            "total_items": len(data),
            "video_count": sum(1 for i in data if i.get("is_video")),
            "by_platform": {},
            "by_keyword": {},
            "top_content": []
        }

        for item in data:
            platform = item.get("platform", "unknown")
            keyword = item.get("keyword", "unknown")
            insights["by_platform"][platform] = insights["by_platform"].get(platform, 0) + 1
            insights["by_keyword"][keyword] = insights["by_keyword"].get(keyword, 0) + 1

        sorted_data = sorted(data, key=lambda x: x.get("likes", 0) or x.get("upvotes", 0), reverse=True)
        insights["top_content"] = sorted_data[:10]

        return insights

    def export_to_json(self, data: List[Dict[str, Any]], summary: Dict[str, Any], filename: str = None) -> str:
        if not filename:
            filename = f"intelligence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        output = {
            "summary": summary,
            "items": data
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        return filename

    async def run(self):
        print("🔍 Phase 1: Initial keyword search...")

        raw_data = await self.gather_intelligence()
        print(f"📊 Gathered {len(raw_data)} items")

        if not raw_data:
            print("⚠️ No data gathered, exiting")
            return []

        print("🤖 Phase 2: AI keyword refinement...")
        refined_keywords = self.ai_refine_keywords(raw_data, SEARCH_KEYWORDS)

        # Phase 3: 二次搜索只用新增的关键词，且最多新增 5 个，避免额度爆炸
        new_keywords = [k for k in refined_keywords if k not in SEARCH_KEYWORDS][:5]
        if new_keywords:
            print(f"🔄 Phase 3: Re-searching with {len(new_keywords)} new keywords...")
            new_data = await self.searcher.search_all(keywords=new_keywords)
            raw_data.extend(new_data)
            print(f"📊 Total: {len(raw_data)} items")
        else:
            print("⏭️ Phase 3: No new keywords, skipping")

        processed = self.process_raw_data(raw_data)

        # Phase 4: 视频分析暂时跳过，避免消耗 Gemini 配额
        # analyzed = await self.analyze_videos(processed)
        analyzed = processed
        print(f"⏭️ Phase 4: Video analysis skipped (enable manually)")

        print("🤖 Phase 5: AI extracting insights...")
        ai_insights = self.ai_extract_insights(analyzed)

        summary = self.enrich_intelligence(analyzed)
        summary["ai_insights"] = ai_insights

        output_file = self.export_to_json(analyzed, summary)
        print(f"💾 Exported to {output_file}")

        return analyzed


async def main():
    processor = IntelligenceProcessor()
    results = await processor.run()
    
    if results:
        print(f"\n📈 Summary:")
        print(f"   Total: {len(results)}")
        if results[0].get("intelligence"):
            stats = results[0]["intelligence"]
            print(f"   By platform: {stats['by_platform']}")
        if results[0].get("ai_insights"):
            insights = results[0]["ai_insights"]
            print(f"   Trends: {insights.get('trends', [])[:5]}")


if __name__ == "__main__":
    asyncio.run(main())