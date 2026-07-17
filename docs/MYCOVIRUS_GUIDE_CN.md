# 真菌病毒科研资讯雷达：中文快速指南

本仓库基于 Paper Distill MCP，针对植物病理学与真菌病毒研究预置了检索主题和筛选偏好。系统会并行检索 OpenAlex、PubMed、Europe PMC、Crossref、bioRxiv、Semantic Scholar 等来源，去重、排序后推送论文摘要，并可衔接 Zotero 与 Obsidian。

## 预置关注方向

- 真菌病毒发现、宏转录组与 mycovirome 多样性
- 植物病原真菌及木霉属相关病毒
- 低毒力、毒力衰减和植物病害生物防治
- RNA 沉默、水平传播及病毒—宿主互作
- Chrysoviridae、Partitiviridae、Totiviridae、Ambiviricota 等分类与进化

配置文件位于 `profiles/mycovirus.json`。关键词采用英文是因为主要文献数据库对英文题录的覆盖和召回更稳定；推送内容仍可由客户端要求用中文总结。

## 推荐安装方式（Codex）

1. 安装 `uv`：<https://docs.astral.sh/uv/getting-started/installation/>
2. 在 `~/.codex/config.toml` 中添加：

```toml
[mcp_servers.paper-distill]
command = "uvx"
args = ["paper-distill-mcp"]

[mcp_servers.paper-distill.env]
OPENALEX_EMAIL = "你的学术邮箱"
```

3. 重启 Codex，输入“初始化 paper-distill”。
4. 让客户端读取本仓库的 `profiles/mycovirus.json`，逐项调用 `add_topic()` 和 `configure()`；也可以直接把 JSON 内容粘贴给客户端并说“按此配置我的研究主题”。

推荐的首次指令：

> 请按 profiles/mycovirus.json 初始化真菌病毒资讯雷达。每天最多推荐 8 篇，用中文给出一句话结论、实验依据、与植物病理学的关系和 DOI；优先近两年的原创研究，排除医学真菌病毒和无关的动物病毒研究。

## 推送渠道

在 MCP 配置的 `env` 区域加入一种渠道即可：

```toml
# Telegram
TELEGRAM_BOT_TOKEN = "..."
TELEGRAM_CHAT_ID = "..."

# 或企业微信
WECOM_WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..."

# 或飞书
FEISHU_WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/..."

# 或 Discord
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/..."
```

凭据只应保存为本机环境变量或 GitHub Secrets，切勿提交到仓库。然后告诉客户端：

> 完成今天的筛选后，调用 send_push，把结果推送到企业微信（或 Telegram/飞书/Discord）。

## 建议的科研工作流

1. 每周运行一次 `pool_refresh()`，收集新论文并去重。
2. 每日执行 `prepare_review()`，按预置主题筛选候选论文。
3. 确认后执行 `finalize_review()`，再调用 `send_push()`。
4. 回复论文编号并调用收藏功能，将重点论文同步到 Zotero 或生成 Obsidian 笔记。
5. 每月检查误报与漏报，调整 `profiles/mycovirus.json` 中的关键词和权重。

## 自动评分与每日日报

每篇论文会获得 0–100 分及 S/A/B/C 四级重要度：

- S（75–100）：重点必读
- A（60–74.9）：高度重要
- B（40–59.9）：值得关注
- C（0–39.9）：一般参考

总分由相关性、时效性、引用影响力和是否首次出现四项组成。系统会同时给出分项分数和中文评分理由，便于人工复核。它是筛选工具，不代表论文质量的最终判断。

本地生成日报：

```bash
python scripts/daily_radar.py
```

输出位于 `output/daily-reports/YYYY-MM-DD.json` 和 `YYYY-MM-DD.md`。Markdown 包含 YAML 属性，可直接放进 Obsidian；JSON 适合接网站、数据库或其他自动化。

仓库自带 `.github/workflows/daily-mycovirus-report.yml`，默认每天北京时间 07:30 运行，并将日报作为 GitHub Actions artifact 保存 90 天。也可在 Actions 页面手动运行。

### GitHub Secrets

在仓库 `Settings → Secrets and variables → Actions` 中配置：

- `OPENALEX_EMAIL`：推荐配置；普通联系邮箱即可，不是 API 密钥。
- `S2_API_KEY`：可选；提高 Semantic Scholar 的稳定性和额度。
- `TELEGRAM_BOT_TOKEN` 与 `TELEGRAM_CHAT_ID`：可选；两者都配置后自动推送日报摘要。

不配置任何私密密钥时，OpenAlex、PubMed、Europe PMC、Crossref、bioRxiv 等基础来源仍可运行，日报会保存在 Actions artifact 中。

## 关键词维护建议

- 将你的核心宿主属名加入 `plant-pathogenic-fungi`，如 `Fusarium`、`Sclerotinia`、`Botrytis`、`Trichoderma`。
- 新病毒类群或 ICTV 分类变化可加入 `taxonomy-evolution`。
- 若医学论文误报较多，在 `custom_focus` 中继续加入排除规则，而不是盲目删除广义关键词。
- 每个主题保留 3–5 组互补检索式；过多近义词会增加重复结果和 API 调用量。

## 数据与费用

OpenAlex、PubMed、Europe PMC、Crossref 和 bioRxiv 等基础检索无需付费。AI 摘要是否产生费用取决于你连接的模型；不配置站点、Zotero 或推送渠道也不影响论文检索。
