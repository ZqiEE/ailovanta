# Open GPU Privacy AI MVP

> 开节点，免费用隐私 AI；不开节点，付费用。

这是一个可以直接本地运行的静态 MVP，用来展示“用户贡献闲置 GPU/CPU 换免费 AI 使用权”的产品飞轮。

## 核心定位

**The user-owned GPU network for private AI.**

用户贡献电脑算力，平台获得低成本 AI 推理、微调和数据处理能力；用户获得免费 AI 使用权。不开节点的用户可以付费使用。

## MVP 功能

- 贡献 GPU 免费用 / 不贡献则付费使用
- 节点贡献比例、节点评分、节点信誉模拟
- 隐私 AI 聊天体验
- 标准模式 / 开放模式 / 创作模式 / 私密陪伴模式
- Prompt、结果、聊天记录阅后即焚
- 本地机器人记忆库
- 机器人记忆一键清空
- 训练引擎模拟：RAG、数据清洗、LoRA/QLoRA、节点分发、模型合并
- 融资叙事页：用户增长 → GPU 增长 → 成本下降 → AI 更强 → 更多用户

## 本地运行

直接双击：

```text
index.html
```

或者：

```bash
python -m http.server 8000
```

然后打开：

```text
http://localhost:8000
```

## 下一步

1. 接入 Ollama + Qwen/Llama 本地推理
2. 接入 Stable Diffusion Worker 文生图
3. 做 Python/Rust 节点客户端
4. 做 FastAPI 调度服务
5. 做 PostgreSQL 节点和用户系统
6. 做机器人 SDK 与本地记忆

## 产品卖点

**免费、隐私、开放、共建、机器人。**
