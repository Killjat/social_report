from typing import List, Dict, Any, Optional
from tikhub import AsyncTikHub
from config import TIKHUB_API_KEY, SEARCH_KEYWORDS, PLATFORMS
import asyncio


class SocialMediaSearcher:
    def __init__(self):
        self.client = AsyncTikHub(api_key=TIKHUB_API_KEY)

    async def search_x(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索 X.com (Twitter) 上的内容"""
        results = []
        try:
            result = await self.client.twitter_web.fetch_search_timeline(
                keyword=keyword,
                search_type="Latest"
            )
            return self._parse_x_results(result, keyword)
        except Exception as e:
            print(f"Error searching X for '{keyword}': {e}")
        return results

    async def search_douyin(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            result = await self.client.douyin_search.fetch_video_search_v2(
                keyword=keyword
            )
            return self._parse_douyin_results(result, keyword)
        except Exception as e:
            print(f"Error searching Douyin for '{keyword}': {e}")
            return []

    async def search_reddit(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            result = await self.client.reddit_app.fetch_dynamic_search(
                query=keyword,
                search_type="link",
                sort="new"
            )
            return self._parse_reddit_results(result, keyword)
        except Exception as e:
            print(f"Error searching Reddit for '{keyword}': {e}")
            return []

    async def search_tiktok(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            result = await self.client.tiktok_app_v3.fetch_video_search_result(
                keyword=keyword,
                count=limit
            )
            return self._parse_tiktok_results(result, keyword)
        except Exception as e:
            print(f"Error searching TikTok for '{keyword}': {e}")
            return []

    async def search_xiaohongshu(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            result = await self.client.xiaohongshu_web.search_notes(
                keyword=keyword,
                page=1
            )
            return self._parse_xiaohongshu_results(result, keyword)
        except Exception as e:
            print(f"Error searching Xiaohongshu for '{keyword}': {e}")
            return []

    def _parse_x_results(self, data: Any, keyword: str) -> List[Dict[str, Any]]:
        results = []
        try:
            items = data.get('data', {}).get('timeline', []) if isinstance(data, dict) else []
            for item in items:
                if not isinstance(item, dict):
                    continue
                tweet_id = item.get('tweet_id', '')
                results.append({
                    "platform": "x",
                    "keyword": keyword,
                    "id": tweet_id,
                    "title": item.get('text', '')[:100],
                    "author": item.get('screen_name', ''),
                    "url": f"https://twitter.com/i/web/status/{tweet_id}",
                    "content": item.get('text', ''),
                    "likes": item.get('favorites', 0),
                    "retweets": item.get('retweets', 0),
                    "replies": item.get('replies', 0),
                    "is_video": False,
                    "created_at": item.get('created_at')
                })
        except Exception as e:
            print(f"Error parsing X results: {e}")
        return results

    def _parse_douyin_results(self, data: Any, keyword: str) -> List[Dict[str, Any]]:
        results = []
        try:
            business_data = data.get('data', {}).get('business_data', []) if isinstance(data, dict) else []
            for entry in business_data:
                if not isinstance(entry, dict):
                    continue
                aweme = entry.get('data', {}).get('aweme_info', {})
                if not aweme:
                    continue
                aweme_id = aweme.get('aweme_id', '')
                author = aweme.get('author', {})
                stats = aweme.get('statistics', {})
                results.append({
                    "platform": "douyin",
                    "keyword": keyword,
                    "id": aweme_id,
                    "title": aweme.get('desc', ''),
                    "author": author.get('nickname', ''),
                    "url": aweme.get('share_url', f"https://www.douyin.com/video/{aweme_id}"),
                    "cover": aweme.get('video', {}).get('cover', {}).get('url_list', [''])[0],
                    "video_url": aweme.get('video', {}).get('play_addr', {}).get('url_list', [''])[0],
                    "likes": stats.get('digg_count', 0),
                    "comments": stats.get('comment_count', 0),
                    "shares": stats.get('share_count', 0),
                    "is_video": True
                })
        except Exception as e:
            print(f"Error parsing Douyin results: {e}")
        return results

    def _parse_reddit_results(self, data: Any, keyword: str) -> List[Dict[str, Any]]:
        results = []
        try:
            edges = (data.get('data', {})
                        .get('search', {})
                        .get('dynamic', {})
                        .get('components', {})
                        .get('main', {})
                        .get('edges', []))
            for edge in edges:
                node = edge.get('node', {})
                children = node.get('children', [])
                for child in children:
                    post = child.get('post', {})
                    if not post:
                        continue
                    post_id = post.get('id', '').replace('t3_', '')
                    results.append({
                        "platform": "reddit",
                        "keyword": keyword,
                        "id": post_id,
                        "title": post.get('postTitle', ''),
                        "author": post.get('authorInfo', {}).get('name', '') if isinstance(post.get('authorInfo'), dict) else '',
                        "url": post.get('url', post.get('permalink', f"https://reddit.com/comments/{post_id}")),
                        "content": post.get('content', {}).get('markdown', '') if isinstance(post.get('content'), dict) else '',
                        "is_video": post.get('isVideo', False),
                        "upvotes": post.get('score', 0),
                        "comments": post.get('commentCount', 0)
                    })
        except Exception as e:
            print(f"Error parsing Reddit results: {e}")
        return results

    def _parse_tiktok_results(self, data: Any, keyword: str) -> List[Dict[str, Any]]:
        results = []
        try:
            search_items = data.get('data', {}).get('search_item_list', []) if isinstance(data, dict) else []
            for entry in search_items:
                if not isinstance(entry, dict):
                    continue
                aweme = entry.get('aweme_info', entry)
                aweme_id = aweme.get('aweme_id', '')
                author = aweme.get('author', {})
                stats = aweme.get('statistics', {})
                results.append({
                    "platform": "tiktok",
                    "keyword": keyword,
                    "id": aweme_id,
                    "title": aweme.get('desc', ''),
                    "author": author.get('nickname', ''),
                    "url": f"https://www.tiktok.com/@{author.get('unique_id', '')}/video/{aweme_id}",
                    "cover": aweme.get('video', {}).get('cover', {}).get('url_list', [''])[0] if aweme.get('video') else '',
                    "video_url": aweme.get('video', {}).get('play_addr', {}).get('url_list', [''])[0] if aweme.get('video') else '',
                    "likes": stats.get('digg_count', 0),
                    "comments": stats.get('comment_count', 0),
                    "shares": stats.get('share_count', 0),
                    "is_video": True
                })
        except Exception as e:
            print(f"Error parsing TikTok results: {e}")
        return results

    def _parse_xiaohongshu_results(self, data: Any, keyword: str) -> List[Dict[str, Any]]:
        results = []
        try:
            items = data.get('data', {}) if isinstance(data, dict) else {}
            if isinstance(items, dict):
                items = items.get('notes', items.get('items', items.get('data', [])))
            for item in items:
                if not isinstance(item, dict):
                    continue
                note_id = item.get('note_id', item.get('id', ''))
                user = item.get('user', {})
                interact = item.get('interact_info', {})
                results.append({
                    "platform": "xiaohongshu",
                    "keyword": keyword,
                    "id": note_id,
                    "title": item.get('title', item.get('display_title', '')),
                    "author": user.get('nickname', user.get('name', '')),
                    "url": f"https://www.xiaohongshu.com/discovery/item/{note_id}",
                    "content": item.get('desc', ''),
                    "likes": interact.get('liked_count', item.get('liked_count', 0)),
                    "comments": interact.get('comment_count', item.get('comment_count', 0)),
                    "is_video": item.get('type', '') == 'video'
                })
        except Exception as e:
            print(f"Error parsing Xiaohongshu results: {e}")
        return results

    async def search_all(self, keywords: List[str] = None, platforms: List[str] = None) -> List[Dict[str, Any]]:
        keywords = keywords or SEARCH_KEYWORDS
        platforms = platforms or PLATFORMS

        all_results = []

        for keyword in keywords:
            for platform in platforms:
                try:
                    if platform == "douyin":
                        results = await self.search_douyin(keyword, limit=1)
                    elif platform == "reddit":
                        results = await self.search_reddit(keyword, limit=1)
                    elif platform == "tiktok":
                        results = await self.search_tiktok(keyword, limit=1)
                    elif platform == "xiaohongshu":
                        results = await self.search_xiaohongshu(keyword, limit=1)
                    elif platform == "x":
                        results = await self.search_x(keyword, limit=1)
                    else:
                        results = []

                    # 每个平台每个关键词只取第 1 条
                    if results:
                        all_results.append(results[0])
                except Exception as e:
                    print(f"Error searching {platform} for '{keyword}': {e}")

        return all_results
