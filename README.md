# 跨境电商情报仪表板

自动从多个社交媒体平台采集跨境电商相关内容，通过 AI 提炼关键词和洞察，并在 Web 仪表板上展示。

## 功能

- 多平台数据采集：抖音、Reddit、X.com（可扩展 TikTok、小红书）
- AI 关键词自动扩展（OpenRouter / DeepSeek）
- AI 内容洞察提取
- 视频封面展示，点击跳转原始链接
- 后台定时自动收集，无需手动触发
- Web 仪表板：平台分布图、关键词热度图、内容列表筛选

## 技术栈

- Python 3.10+
- Flask（Web 服务）
- TikHub SDK（社交媒体数据）
- Google Gemini（视频内容分析，可选）
- OpenRouter / DeepSeek（关键词分析）
- Chart.js（前端图表）

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Keys

复制 `.env.example` 为 `.env`，填入你的 API Keys：

```bash
cp .env.example .env
```

```env
TIKHUB_API_KEY=your_tikhub_api_key
GEMINI_API_KEY=your_gemini_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

| Key | 获取地址 | 用途 |
|-----|---------|------|
| TIKHUB_API_KEY | [tikhub.io](https://tikhub.io) | 社交媒体数据采集 |
| GEMINI_API_KEY | [aistudio.google.com](https://aistudio.google.com/apikey) | 视频内容分析（可选） |
| OPENROUTER_API_KEY | [openrouter.ai](https://openrouter.ai) | 关键词分析与洞察提取 |

### 3. 启动仪表板

```bash
python web_dashboard.py
```

访问 [http://localhost:8888](http://localhost:8888)

服务启动后会自动开始首次数据采集，之后每 60 分钟自动收集一次。

也可以在仪表板页面点击「立即收集」手动触发。

## 配置说明

编辑 `config.py` 调整采集范围：

```python
# 搜索关键词
SEARCH_KEYWORDS = [
    "跨境电商",
    "Amazon",
    "Shopify",
    ...
]

# 采集平台：douyin / reddit / x / tiktok / xiaohongshu
PLATFORMS = ["douyin", "reddit", "x"]
```

## 费用估算

每次完整采集约消耗：

| 服务 | 调用次数 | 费用 |
|------|---------|------|
| TikHub | ~45 次 | ~$0.12 |
| OpenRouter | 2 次 | ~$0.01 |
| Gemini | 0（默认关闭） | $0 |
| **合计** | | **~$0.13** |

## 项目结构

```
├── main.py              # 主流程编排
├── searcher.py          # 多平台数据采集
├── analyzer.py          # Gemini 视频分析
├── keyword_analyzer.py  # AI 关键词分析
├── web_dashboard.py     # Flask Web 服务
├── config.py            # 配置（关键词、平台）
├── templates/
│   └── dashboard.html   # 前端仪表板
├── .env.example         # 环境变量模板
└── requirements.txt     # 依赖列表
```

## 注意事项

- `.env` 文件含有 API Keys，已加入 `.gitignore`，**不会上传到 GitHub**
- 采集到的数据文件（`intelligence_*.json`）同样不会上传
- TikHub 按调用次数计费，建议先用少量关键词测试
