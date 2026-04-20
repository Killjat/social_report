import json
import requests
from typing import List, Dict, Any
from config import OPENROUTER_API_KEY


class KeywordAnalyzer:
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "deepseek/deepseek-chat"

    def analyze_and_expand(self, collected_data: List[Dict[str, Any]], current_keywords: List[str]) -> List[str]:
        if not collected_data:
            return current_keywords

        sample_content = self._prepare_sample(collected_data)
        
        prompt = f"""你是一个跨境电商情报专家。请分析以下已收集的社交媒体内容，判断哪些关键词最有价值，并建议新的搜索关键词。

已收集内容样例：
{sample_content}

当前使用的关键词：{', '.join(current_keywords)}

请按以下JSON格式返回分析结果：
{{
    "insights": "简短总结这些内容揭示的跨境电商趋势",
    "suggested_keywords": ["新关键词1", "新关键词2", ...],
    "prioritized_topics": ["最重要的话题1", "最重要的话题2"]
}}

只返回JSON，不要其他内容。"""

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://cyberreport.local",
                    "X-Title": "CyberReport"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                },
                timeout=30
            )
            
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            return self._parse_response(content, current_keywords)
            
        except Exception as e:
            print(f"Error analyzing keywords: {e}")
            return current_keywords

    def _prepare_sample(self, data: List[Dict[str, Any]], max_items: int = 10) -> str:
        samples = []
        for item in data[:max_items]:
            title = item.get("title", item.get("content", ""))[:200]
            platform = item.get("platform", "")
            samples.append(f"- [{platform}] {title}")
        return "\n".join(samples)

    def _parse_response(self, response: str, current_keywords: List[str]) -> List[str]:
        try:
            json_str = response.strip().split("```json")[1].split("```")[0] if "```json" in response else response
            parsed = json.loads(json_str)
            
            new_keywords = current_keywords.copy()
            for kw in parsed.get("suggested_keywords", []):
                if kw not in new_keywords:
                    new_keywords.append(kw)
            
            return new_keywords
            
        except Exception as e:
            print(f"Error parsing AI response: {e}")
            return current_keywords

    def extract_insights(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not data:
            return {"insights": "No data to analyze", "trends": []}

        sample_content = self._prepare_sample(data)
        
        prompt = f"""分析以下跨境电商社交媒体内容，提取关键情报：

{sample_content}

请返回JSON格式：
{{
    "trends": ["趋势1", "趋势2", ...],
    "products": ["产品1", "产品2", ...],
    "platforms": ["平台1", "平台2", ...],
    "marketing_tactics": ["策略1", "策略2", ...],
    "summary": "一句话总结"
}}"""

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://cyberreport.local",
                    "X-Title": "CyberReport"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.5
                },
                timeout=30
            )
            
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            return json.loads(content)
            
        except Exception as e:
            print(f"Error extracting insights: {e}")
            return {"trends": [], "products": [], "platforms": [], "summary": ""}