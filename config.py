import os
from dotenv import load_dotenv

load_dotenv()

TIKHUB_API_KEY = os.getenv("TIKHUB_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

SEARCH_KEYWORDS = [
    "跨境电商",
    "海外电商",
    "跨境物流",
    "Amazon",
    "Shopify",
    "TikTok Shop",
    "eBay",
    "速卖通",
    "跨境营销",
    "跨境支付"
]

PLATFORMS = ["douyin", "reddit", "x"]

