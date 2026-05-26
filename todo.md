# TrendScout Commerce — 下一步行动计划

## 一、真实 API 接入

### 1. Google Trends API（Alpha）

- **文档**: https://developers.google.com/search/apis/trends
- **接入方式**: 申请 Google Cloud 项目，开启 Trends API alpha 白名单
- **替换位置**: `src/hotcommerce/sources.py` → `GoogleTrendsAdapter`
- **关键字段**: `interest_over_time`, `related_queries`, `geo` (区域过滤)
- **认证**: OAuth 2.0 Service Account，密钥存入 GitHub Actions Secret `GOOGLE_TRENDS_API_KEY`
- **注意**: Alpha 阶段有配额限制，建议每次 ETL 批量请求并本地缓存 `data/cache/trends/`

### 2. Reddit API（OAuth）

- **文档**: https://www.reddit.com/dev/api/
- **接入方式**: 在 Reddit 开发者后台创建 App，获取 `client_id` / `client_secret`
- **替换位置**: `src/hotcommerce/sources.py` → `RedditAdapter`
- **推荐端点**:
  - `GET /r/{subreddit}/hot` — 板块热帖
  - `GET /search` — 关键词跨版搜索
  - `GET /r/{subreddit}/comments/{id}` — 评论情绪分析原料
- **认证**: `client_credentials` 流，Token 自动刷新，存入 Secret `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET`
- **速率限制**: 60 req/min，ETL 侧加指数退避

### 3. TikTok Research API

- **文档**: https://developers.tiktok.com/products/research-api/
- **接入方式**: 申请 TikTok for Developers Research API 资格（需机构邮箱审核）
- **替换位置**: `src/hotcommerce/sources.py` → `TikTokAdapter`
- **关键端点**:
  - `POST /research/video/query/` — 按关键词/标签查热度视频
  - `POST /research/user/liked_videos/` — 达人互动数据
- **认证**: Client Key + Secret，存入 Secret `TIKTOK_CLIENT_KEY` / `TIKTOK_CLIENT_SECRET`
- **字段映射**: `like_count`, `comment_count`, `share_count`, `create_time` → `social_velocity_score`

### 4. Amazon PA-API 5.0（Product Advertising API）

- **文档**: https://webservices.amazon.com/paapi5/documentation/
- **接入方式**: 需要 Amazon Associates 账号，申请 PA-API 5.0 访问
- **替换位置**: `src/hotcommerce/sources.py` → `AmazonAdapter`
- **关键操作**:
  - `SearchItems` — 按关键词搜商品，获取 BSR（Best Seller Rank）
  - `GetItems` — 按 ASIN 获取详情、价格、评分、评论数
- **认证**: `AWS_ACCESS_KEY` + `AWS_SECRET_KEY` + `PARTNER_TAG`，存入 Secret
- **区域支持**: `amazon.com`, `amazon.co.uk`, `amazon.co.jp`, `amazon.de` 分站独立请求

### 5. 环境变量汇总（`.env.example` 更新）

```env
GOOGLE_TRENDS_API_KEY=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
TIKTOK_CLIENT_KEY=
TIKTOK_CLIENT_SECRET=
AMAZON_ACCESS_KEY=
AMAZON_SECRET_KEY=
AMAZON_PARTNER_TAG=
OPENAI_API_KEY=          # AI 报告生成
ANTHROPIC_API_KEY=       # 备选 Claude 模型
```

---

## 二、AI 自动 PDF 报告流程

### 目标

每次 ETL 完成后，自动为 Top N 商品生成结构化 PDF 报告，包含：
- 商品基本信息 + 评分明细
- 多源趋势图（折线图）
- AI 撰写的市场分析与展望段落
- 品牌/竞品对比表

### 流程设计

```
ETL 完成
  │
  ▼
data/out/rankings_month.json + reports_month.md
  │
  ▼
scripts/generate_pdf_report.py
  │
  ├─ 读取 rankings + products JSONL
  ├─ 调用 AI API 生成分析段落（Claude / GPT-4o）
  ├─ 用 Jinja2 渲染 HTML 模板
  ├─ 用 WeasyPrint 或 Playwright 将 HTML → PDF
  └─ 输出 data/out/report_<window>_<date>.pdf
```

### 实现步骤

#### Step 1 — AI 报告段落生成（`src/hotcommerce/ai_reporter.py`）

```python
# 伪代码示意
def generate_market_analysis(product: Product, top_signals: dict) -> str:
    prompt = f"""
    商品名称: {product.name}
    类目: {product.category}
    综合评分: {product.score:.2f}
    热度信号: {top_signals}

    请用200字以内，以专业电商分析师视角撰写该商品的市场分析与未来3个月展望。
    要求：简洁、数据驱动、指出风险与机会。
    """
    # 调用 anthropic SDK，使用 claude-sonnet-4-6
    # 开启 prompt cache（system prompt 固定部分加 cache_control）
```

- 使用 `anthropic` SDK，模型 `claude-sonnet-4-6`
- 为固定 system prompt 开启 **prompt caching**，降低批量生成成本
- 支持异步并发（`asyncio` + `anyio`），Top 20 商品并发生成，控制 max_concurrency=5

#### Step 2 — HTML 模板（`src/hotcommerce/templates/report.html.j2`）

```
封面: Logo + 报告标题 + 生成日期 + 区域
目录: 自动生成
每个商品一页:
  - 商品名 / ASIN / 类目 / 评分雷达图（Chart.js SVG）
  - 各源信号评分明细表
  - AI 市场分析段落（Markdown → HTML）
  - 趋势折线图（过去30天搜索热度）
  - 竞品对比（同类目 Top 3）
附录: 数据来源说明 + 评分方法论
```

#### Step 3 — PDF 渲染

- 推荐 **WeasyPrint**（纯 Python，无需浏览器）: `pip install weasyprint`
- 备选 **Playwright**（忠实渲染 Chart.js 动态图）: `pip install playwright && playwright install chromium`
- 输出路径: `data/out/report_month_2026-05.pdf`

#### Step 4 — GitHub Actions 集成（`.github/workflows/monthly-etl.yml` 扩展）

```yaml
- name: Generate PDF Report
  run: |
    python scripts/generate_pdf_report.py \
      --rankings data/out/rankings_month.json \
      --products data/out/products_month.jsonl \
      --output data/out/report_month_$(date +%Y-%m).pdf
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

- name: Upload PDF Report
  uses: actions/upload-artifact@v4
  with:
    name: pdf-report-${{ github.run_id }}
    path: data/out/report_*.pdf
    retention-days: 90
```

### 新增依赖（`pyproject.toml`）

```toml
[project.optional-dependencies]
pdf = [
  "anthropic>=0.40.0",
  "jinja2>=3.1",
  "weasyprint>=62.0",
  "markdown>=3.6",
  "matplotlib>=3.9",   # 趋势图生成
]
```

安装: `pip install -e ".[pdf]"`

---

## 三、优先级排序

| 优先级 | 任务 | 预估工时 |
|--------|------|---------|
| P0 | Reddit API 接入（审核最快） | 1天 |
| P0 | AI 报告段落生成模块 | 1天 |
| P1 | PDF 渲染 + HTML 模板 | 2天 |
| P1 | Amazon PA-API 接入 | 2天 |
| P2 | Google Trends API 接入（需白名单） | 待批 |
| P2 | TikTok Research API 接入（需审核） | 待批 |
| P3 | GitHub Actions PDF 上传 | 0.5天 |

---

## 四、验收标准

- [ ] 每个真实 API adapter 有对应单元测试，mock 可与真实响应结构互换
- [ ] `generate_pdf_report.py --dry-run` 用 mock 数据端到端跑通，输出合法 PDF
- [ ] AI 报告生成单次成本 < $0.10（Top 20 商品，使用 prompt cache）
- [ ] GitHub Actions 月度运行总时长 < 15 分钟
- [ ] PDF 报告文件大小 < 5MB
