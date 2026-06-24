# Ailovanta 下一阶段产品需求文档

版本：v1.11.0 Guest Chat Core  
阶段目标：打开即用、无登录、无付费、先证明产品价值

## 1. 阶段定位

Ailovanta 下一阶段不做登录、不做付费、不做钱包、不做复杂企业功能。

当前阶段只做一件事：

让用户打开网页后，能够像使用 ChatGPT 一样，直接开始聊天，并且聊天记录能被保存、能继续上下文、能稳定使用。

核心原则：

```text
First prove value.
Then add identity.
Then add payment.
```

也就是：

```text
先让人觉得好用
再考虑登录
再考虑付费
```

## 2. 当前阶段不做什么

本阶段明确不做：

```text
不强制 GitHub 登录
不接邮箱登录
不接手机号登录
不接钱包登录
不接 Stripe / Paddle / 支付宝 / 微信支付
不做订阅套餐
不做付费墙
不做企业合同
不做 token / staking / reward payout
```

GitHub OAuth 后端可以保留，但不作为默认用户路径。

## 3. 用户默认路径

用户打开 Ailovanta 后，应该直接看到聊天界面。

理想流程：

```text
1. 用户打开网页
2. 系统自动生成 guest_id
3. 用户直接输入问题
4. 前端调用 POST /ailovanta/v1/chat
5. 后端创建或复用 conversation_id
6. 后端保存 user message
7. 后端读取历史上下文
8. 后端调用本地模型 / Ollama / fallback
9. 后端保存 assistant message
10. 前端展示回答
11. 用户可以继续追问
```

用户不需要知道 guest_id、conversation_id、session、token、钱包、节点等技术细节。

## 4. 核心产品目标

下一阶段要把 Ailovanta 从“能保存聊天”推进到“能连续聊天”。

当前已有：

```text
Guest Mode
/ailovanta/v1/chat
ConversationStore
conversation_id
message 保存
前端 guest_id
```

下一阶段要补齐：

```text
多轮上下文注入
前端会话列表
继续历史会话
删除会话
流式输出基础能力
更像 ChatGPT 的聊天体验
```

## 5. P0 必做需求

### P0-1：多轮上下文注入

当前问题：

```text
虽然已经保存 conversation messages，
但模型回答时还没有真正利用历史上下文。
```

目标：

当用户继续对话时，后端应该读取同一个 conversation_id 下的历史消息，并把最近若干轮拼进模型输入。

实现要求：

```text
新增 context builder
读取最近 N 条消息
按 user / assistant 角色拼接
控制最大上下文长度
传给 OllamaAdapter
fallback 时也返回明确说明
```

建议新增文件：

```text
api/conversation_context.py
```

建议函数：

```python
build_chat_context(messages: list[dict], latest_prompt: str, max_messages: int = 12) -> list[dict]
```

`/ailovanta/v1/chat` 应该改为：

```text
先获取 conversation
保存用户消息
读取历史 messages
构造上下文
调用模型
保存 assistant 回复
返回 answer + conversation_id
```

验收标准：

```text
用户问：“我刚才说了什么？”
系统能根据当前 conversation 历史回答。
```

### P0-2：前端显示历史会话

当前问题：

```text
前端只保存一个 conversation_id，
用户看不到历史会话列表。
```

目标：

Chat 页面右侧或顶部显示当前 guest_id 下的会话列表。

前端调用：

```text
GET /ailovanta/v1/conversations?user_id=guest_xxx
GET /ailovanta/v1/conversations/{conversation_id}/messages
```

功能：

```text
新建聊天
切换聊天
读取历史消息
删除当前聊天
```

验收标准：

```text
刷新页面后，用户还能看到之前的会话。
点击历史会话后，消息能恢复到聊天窗口。
```

### P0-3：前端真实调用后端聊天

当前前端已经调用：

```text
POST /ailovanta/v1/chat
```

下一步要增强：

```text
请求失败时展示清楚错误
API 未启动时提示启动命令
发送中禁用按钮
回答成功后更新 conversation_id
读取历史会话后继续对话
```

验收标准：

```text
打开 /app
输入问题
点击 Send
后端返回 answer
前端展示 answer
刷新后还能继续
```

### P0-4：保留 fallback，但提示真实状态

当前 fallback 不能装成真模型。

如果没有接 Ollama，回答应该明确：

```text
Ailovanta local fallback: connect Ollama or a registered runtime to enable real model responses.
```

不能假装已经是强 AI。

验收标准：

```text
没有 Ollama 时，不报错，不白屏，不假装 ChatGPT。
有 Ollama 时，能返回本地模型结果。
```

## 6. P1 重要需求

### P1-1：流式输出

目标：

让聊天体验更像 ChatGPT。

接口可先做：

```text
POST /ailovanta/v1/chat/stream
```

或者先在前端做假流式显示，但必须标注是本地渲染，不要伪装模型流。

真正流式后端可以后续接：

```text
StreamingResponse
Ollama streaming
SSE
```

### P1-2：会话标题自动生成

当前 title 默认是：

```text
Guest chat
```

下一阶段可以用第一条用户消息生成标题：

```text
前 20-30 个字符作为标题
```

例如：

```text
用户问：怎么用分布式算力跑 AI？
标题：怎么用分布式算力跑 AI
```

### P1-3：清空 guest 数据

前端提供：

```text
Reset guest id
Clear current chat
Delete conversation
```

后端已有 DELETE conversation，可以接前端按钮。

### P1-4：产品状态提示

首页或 Chat 页面显示：

```text
Guest mode
No login required
No payment required
Local MVP
Ollama connected / fallback mode
```

避免用户误解成已经是完整全球 AI 网络。

## 7. 后端接口要求

当前必须保留并可用：

```text
POST /ailovanta/v1/chat
GET  /ailovanta/v1/conversations
GET  /ailovanta/v1/conversations/{conversation_id}/messages
DELETE /ailovanta/v1/conversations/{conversation_id}

POST /ailovanta/v1/run
POST /v1/chat/completions

GET  /reputation/leaderboard
GET  /reputation/summary

POST /usage/events
GET  /usage/events
GET  /usage/summary
```

不能再出现因为重写 `api/main.py` 导致旧测试接口 404 的问题。

## 8. 测试要求

必须新增或更新测试：

```text
tests/test_conversation_context.py
tests/test_guest_chat_flow.py
tests/test_frontend_markers.py
```

重点测试：

```text
guest chat 创建 conversation
同一个 conversation 可继续对话
history messages 可读取
context builder 会带上上一轮消息
reputation endpoints 不丢
usage endpoints 不丢
validate.py 不检查过时文案
```

CI 必须通过：

```bash
python validate.py
python -m pytest -q
```

## 9. 前端要求

`index.html` 下一阶段要像一个真正聊天产品，而不是展示页。

页面结构建议：

```text
左侧：会话列表
中间：聊天窗口
底部：输入框
右侧/顶部：Guest session 状态
```

最小可用功能：

```text
New chat
Conversation list
Load conversation
Delete conversation
Send message
Clear current view
Guest id display
API status display
```

不要再把“节点贡献/付费模式”放在用户开始聊天前面。

节点功能可以放到单独 tab，不阻挡聊天。

## 10. 不要做的错误方向

不要现在做：

```text
复杂登录系统
收费系统
钱包系统
企业后台
漂亮但不能用的 landing page
假数据过多的 dashboard
过度包装“全球分布式网络已完成”
```

当前核心不是吹概念，是让用户真的能聊起来。

## 11. 下一阶段最终验收标准

完成后，用户体验应该是：

```text
打开 Ailovanta
不用登录
不用付费
直接输入问题
得到回答
刷新页面
历史还在
继续追问
系统能理解前文
```

开发验收：

```text
python validate.py 通过
python -m pytest -q 通过
/app 可打开
/ailovanta/v1/chat 可用
conversation history 可用
context injection 可用
无登录墙
无付费墙
```

## 12. 下一阶段一句话目标

把 Ailovanta 做成一个“打开即用、有历史、有上下文、能持续聊天”的 Guest-first AI 产品，而不是一个需要登录、需要付费、还没证明价值的概念 Demo。
