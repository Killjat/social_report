"""
深度发散搜索模块
输入一个关键词/事件，在多个平台并行搜索，返回结构化结果
支持：微博、知乎、抖音、X.com、Reddit、FOFA
"""

import asyncio
import base64
import json
import re
import requests
from typing import List, Dict, Any, Optional
from tikhub import AsyncTikHub
from config import TIKHUB_API_KEY
from dotenv import load_dotenv
import os

load_dotenv()

FOFA_EMAIL = os.getenv("FOFA_EMAIL", "")
FOFA_KEY = os.getenv("FOFA_KEY", "")


class DeepSearcher:
    def __init__(self):
        self.client = AsyncTikHub(api_key=TIKHUB_API_KEY)

    # ─── 微博 ────────────────────────────────────────────────
    async def search_weibo(self, keyword: str, limit: int = 10) -> List[Dict]:
        results = []
        try:
            r = await self.client.weibo_web.fetch_search(keyword=keyword)
            cards = r.get("data", {}).get("data", {}).get("cards", [])
            for card in cards:
                # 顶层 mblog
                if card.get("mblog"):
                    results.append(self._parse_weibo_mblog(card["mblog"], keyword))
                # card_group 里的 mblog
                for sub in card.get("card_group", []):
                    if sub.get("mblog"):
                        results.append(self._parse_weibo_mblog(sub["mblog"], keyword))
                if len(results) >= limit:
                    break
        except Exception as e:
            print(f"[weibo] 搜索失败: {e}")
        return results[:limit]

    def _parse_weibo_mblog(self, mblog: dict, keyword: str) -> Dict:
        # 去除 HTML 标签
        text = re.sub(r"<[^>]+>", "", mblog.get("text", ""))
        return {
            "platform": "weibo",
            "keyword": keyword,
            "id": str(mblog.get("id", "")),
            "title": text[:100],
            "content": text,
            "author": mblog.get("user", {}).get("screen_name", ""),
            "url": f"https://weibo.com/{mblog.get('user',{}).get('id','')}/{mblog.get('bid','')}",
            "likes": mblog.get("attitudes_count", 0),
            "comments": mblog.get("comments_count", 0),
            "retweets": mblog.get("reposts_count", 0),
            "created_at": mblog.get("created_at", ""),
            "is_video": False,
        }

    # ─── 知乎 ────────────────────────────────────────────────
    async def search_zhihu(self, keyword: str, limit: int = 10) -> List[Dict]:
        results = []
        try:
            r = await self.client.zhihu_web.fetch_article_search_v3(keyword=keyword)
            items = r.get("data", {}).get("data", [])
            for item in items:
                obj = item.get("object", {})
                # hot_timing 类型里有 content_items
                if obj.get("type") == "hot_timing":
                    for ci in obj.get("content_items", [])[:3]:
                        inner = ci.get("object", {})
                        if inner.get("title"):
                            results.append({
                                "platform": "zhihu",
                                "keyword": keyword,
                                "id": str(inner.get("id", "")),
                                "title": inner.get("title", ""),
                                "content": re.sub(r"<[^>]+>", "", inner.get("excerpt", ""))[:200],
                                "author": inner.get("author", {}).get("name", "") if isinstance(inner.get("author"), dict) else "",
                                "url": inner.get("url", "").replace("api.zhihu.com/articles", "zhuanlan.zhihu.com/p"),
                                "likes": inner.get("voteup_count", 0),
                                "comments": inner.get("comment_count", 0),
                                "is_video": False,
                            })
                # 普通文章/回答
                elif obj.get("title"):
                    results.append({
                        "platform": "zhihu",
                        "keyword": keyword,
                        "id": str(obj.get("id", "")),
                        "title": obj.get("title", ""),
                        "content": re.sub(r"<[^>]+>", "", obj.get("excerpt", ""))[:200],
                        "author": obj.get("author", {}).get("name", "") if isinstance(obj.get("author"), dict) else "",
                        "url": obj.get("url", ""),
                        "likes": obj.get("voteup_count", 0),
                        "comments": obj.get("comment_count", 0),
                        "is_video": False,
                    })
                if len(results) >= limit:
                    break
        except Exception as e:
            print(f"[zhihu] 搜索失败: {e}")
        return results[:limit]

    # ─── 抖音 ────────────────────────────────────────────────
    async def search_douyin(self, keyword: str, limit: int = 10) -> List[Dict]:
        results = []
        try:
            r = await self.client.douyin_search.fetch_video_search_v2(keyword=keyword)
            biz = r.get("data", {}).get("business_data", [])
            for entry in biz:
                aweme = entry.get("data", {}).get("aweme_info", {})
                if not aweme:
                    continue
                aweme_id = aweme.get("aweme_id", "")
                author = aweme.get("author", {})
                stats = aweme.get("statistics", {})
                results.append({
                    "platform": "douyin",
                    "keyword": keyword,
                    "id": aweme_id,
                    "title": aweme.get("desc", ""),
                    "author": author.get("nickname", ""),
                    "url": aweme.get("share_url", f"https://www.douyin.com/video/{aweme_id}"),
                    "cover": aweme.get("video", {}).get("cover", {}).get("url_list", [""])[0],
                    "likes": stats.get("digg_count", 0),
                    "comments": stats.get("comment_count", 0),
                    "shares": stats.get("share_count", 0),
                    "is_video": True,
                })
                if len(results) >= limit:
                    break
        except Exception as e:
            print(f"[douyin] 搜索失败: {e}")
        return results[:limit]

    # ─── X.com ───────────────────────────────────────────────
    async def search_x(self, keyword: str, limit: int = 10) -> List[Dict]:
        results = []
        try:
            r = await self.client.twitter_web.fetch_search_timeline(keyword=keyword, search_type="Latest")
            tweets = r.get("data", {}).get("timeline", [])
            for t in tweets:
                if not isinstance(t, dict):
                    continue
                tweet_id = t.get("tweet_id", "")
                results.append({
                    "platform": "x",
                    "keyword": keyword,
                    "id": tweet_id,
                    "title": t.get("text", "")[:100],
                    "content": t.get("text", ""),
                    "author": t.get("screen_name", ""),
                    "url": f"https://twitter.com/i/web/status/{tweet_id}",
                    "likes": t.get("favorites", 0),
                    "retweets": t.get("retweets", 0),
                    "replies": t.get("replies", 0),
                    "created_at": t.get("created_at", ""),
                    "is_video": False,
                })
                if len(results) >= limit:
                    break
        except Exception as e:
            print(f"[x] 搜索失败: {e}")
        return results[:limit]

    # ─── Reddit ──────────────────────────────────────────────
    async def search_reddit(self, keyword: str, limit: int = 10) -> List[Dict]:
        results = []
        try:
            r = await self.client.reddit_app.fetch_dynamic_search(query=keyword, search_type="link", sort="new")
            edges = (r.get("data", {}).get("search", {})
                      .get("dynamic", {}).get("components", {})
                      .get("main", {}).get("edges", []))
            for edge in edges:
                for child in edge.get("node", {}).get("children", []):
                    post = child.get("post", {})
                    if not post:
                        continue
                    post_id = post.get("id", "").replace("t3_", "")
                    results.append({
                        "platform": "reddit",
                        "keyword": keyword,
                        "id": post_id,
                        "title": post.get("postTitle", ""),
                        "content": post.get("content", {}).get("markdown", "")[:200] if isinstance(post.get("content"), dict) else "",
                        "author": post.get("authorInfo", {}).get("name", "") if isinstance(post.get("authorInfo"), dict) else "",
                        "url": post.get("url", f"https://reddit.com/comments/{post_id}"),
                        "upvotes": post.get("score", 0),
                        "comments": post.get("commentCount", 0),
                        "is_video": post.get("isVideo", False),
                    })
                    if len(results) >= limit:
                        break
        except Exception as e:
            print(f"[reddit] 搜索失败: {e}")
        return results[:limit]

    # ─── FOFA ────────────────────────────────────────────────
    def search_fofa(self, query: str, limit: int = 10) -> List[Dict]:
        """FOFA 资产搜索，query 支持 FOFA 语法，如 domain="pinduoduo.com" """
        results = []
        if not FOFA_EMAIL or not FOFA_KEY:
            print("[fofa] 未配置 FOFA_EMAIL / FOFA_KEY")
            return results
        try:
            q_b64 = base64.b64encode(query.encode()).decode()
            resp = requests.get(
                "https://fofa.info/api/v1/search/all",
                params={
                    "email": FOFA_EMAIL,
                    "key": FOFA_KEY,
                    "qbase64": q_b64,
                    "size": limit,
                    "fields": "host,title,ip,domain,port,country,server,lastupdatetime"
                },
                timeout=15
            )
            data = resp.json()
            for row in data.get("results", []):
                host, title, ip, domain, port, country, server, updated = (row + [""] * 8)[:8]
                results.append({
                    "platform": "fofa",
                    "keyword": query,
                    "id": host,
                    "title": title,
                    "host": host,
                    "ip": ip,
                    "domain": domain,
                    "port": port,
                    "country": country,
                    "server": server,
                    "updated": updated,
                    "url": f"http://{host}" if not host.startswith("http") else host,
                    "total_assets": data.get("size", 0),
                })
        except Exception as e:
            print(f"[fofa] 搜索失败: {e}")
        return results

    # ─── 全平台发散搜索 ───────────────────────────────────────
    async def deep_search(
        self,
        keyword: str,
        keyword_en: Optional[str] = None,
        fofa_query: Optional[str] = None,
        platforms: Optional[List[str]] = None,
        limit_per_platform: int = 10,
    ) -> Dict[str, Any]:
        """
        多平台发散搜索
        :param keyword: 中文关键词（用于微博、知乎、抖音）
        :param keyword_en: 英文关键词（用于 X.com、Reddit）
        :param fofa_query: FOFA 查询语法（如 domain="pinduoduo.com"）
        :param platforms: 指定平台列表，默认全部
        :param limit_per_platform: 每个平台最多返回条数
        """
        kw_en = keyword_en or keyword
        all_platforms = ["weibo", "zhihu", "douyin", "x", "reddit", "fofa"]
        target = platforms or all_platforms

        tasks = {}
        if "weibo" in target:
            tasks["weibo"] = self.search_weibo(keyword, limit_per_platform)
        if "zhihu" in target:
            tasks["zhihu"] = self.search_zhihu(keyword, limit_per_platform)
        if "douyin" in target:
            tasks["douyin"] = self.search_douyin(keyword, limit_per_platform)
        if "x" in target:
            tasks["x"] = self.search_x(kw_en, limit_per_platform)
        if "reddit" in target:
            tasks["reddit"] = self.search_reddit(kw_en, limit_per_platform)

        # 并发跑异步任务
        results = {}
        if tasks:
            gathered = await asyncio.gather(*tasks.values(), return_exceptions=True)
            for platform, result in zip(tasks.keys(), gathered):
                results[platform] = result if isinstance(result, list) else []

        # FOFA 是同步的，单独跑
        if "fofa" in target:
            fq = fofa_query or f'"{keyword}"'
            results["fofa"] = self.search_fofa(fq, limit_per_platform)

        # 汇总统计
        total = sum(len(v) for v in results.values())
        summary = {
            "keyword": keyword,
            "keyword_en": kw_en,
            "total": total,
            "by_platform": {p: len(v) for p, v in results.items()},
        }

        return {
            "summary": summary,
            "results": results,
        }


# ─── 便捷函数 ─────────────────────────────────────────────────
async def deep_search(keyword: str, keyword_en: str = None, fofa_query: str = None,
                      platforms: List[str] = None, limit: int = 10) -> Dict:
    searcher = DeepSearcher()
    return await searcher.deep_search(keyword, keyword_en, fofa_query, platforms, limit)


if __name__ == "__main__":
    async def main():
        print("🔍 发散搜索: 拼多多罚款\n")
        result = await deep_search(
            keyword="拼多多罚款",
            keyword_en="Pinduoduo fine regulatory",
            fofa_query='domain="pinduoduo.com" || domain="temu.com"',
            limit=5
        )
        print(f"总计: {result['summary']['total']} 条")
        print(f"各平台: {result['summary']['by_platform']}\n")
        for platform, items in result["results"].items():
            print(f"【{platform.upper()}】")
            for item in items:
                print(f"  {item.get('author','')}: {item.get('title','')[:60]}")
                print(f"  👍{item.get('likes') or item.get('upvotes',0)}  💬{item.get('comments',0)}  🔗{item.get('url','')[:60]}")
            print()

    asyncio.run(main())
