# 电商客服 Agent

多 Agent 协作的智能客服系统。用户用自然语言提问，系统自动识别意图，路由到对应的专业客服 Agent，调用订单/物流/售后系统查询后回复，并经审核节点校验。
这是第四个仿电商客服的项目，里面的内容是通过模型虚构出来的，如果需要可以替换。

## 功能

- **意图识别**：自动判断问题属于 售前 / 物流 / 售后 / 闲聊
- **智能路由**：LangGraph 编排，按意图分发到对应专业 Agent
- **工具调用**：查询订单、物流、商品、售后工单
- **回复审核**：独立节点校验回复，防止编造信息
- **多轮对话**：支持用户提供订单号、手机号等上下文

##  架构

```
用户问题
   ↓
意图识别（售前/物流/售后/闲聊）
   ↓
路由到专业 Agent
   ├── 售前 Agent  → query_product
   ├── 物流 Agent  → query_order / query_logistics / query_customer_orders
   ├── 售后 Agent  → query_order / query_after_sales
   └── 闲聊节点
   ↓
回复审核（检查是否编造、是否答非所问）
   ↓
返回用户
```

##  快速开始

### 1. 克隆项目

```bash
git clone https://github.com/yuchentongqi/ecommerce-customer-service-agent.git
cd ecommerce-customer-service-agent
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

在项目根目录创建 `.env`：

```
DASHSCOPE_API_KEY=sk-你的Key
MODEL_NAME=qwen3.7-flash
BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

没有 Key？去 [阿里云百炼](https://bailian.console.aliyun.com/) 免费注册获取。

### 5. 生成模拟数据库

```bash
python scripts/init_db.py
```

### 6. 启动

```bash
python app.py
```

浏览器打开 `http://127.0.0.1:7860`。

##  使用示例

| 问题 | 意图 | 调用工具 |
|---|---|---|
| 无线蓝牙耳机多少钱？ | 售前 | query_product |
| 我的订单 1002 到哪了？ | 物流 | query_logistics |
| 订单 1005 退款处理得怎么样了？ | 售后 | query_after_sales |
| 你好呀 | 闲聊 | — |

##  项目结构

```
ecommerce-customer-service-agent/
├── app.py                  # Gradio 界面入口
├── agent/
│   ├── __init__.py
│   ├── graph.py            # LangGraph 工作流编排
│   ├── nodes.py            # 意图识别 / 专业 Agent / 审核节点
│   └── tools.py            # 工具函数（订单、物流、商品、售后）
├── data/
│   └── shop.db             # SQLite 模拟商城数据库
├── scripts/
│   └── init_db.py          # 生成模拟数据
├── .gitignore
├── requirements.txt
└── README.md
```

##  技术栈

| 组件 | 用途 |
|---|---|
| [LangGraph](https://github.com/langchain-ai/langgraph) | 多 Agent 工作流编排 |
| [LangChain](https://github.com/langchain-ai/langchain) | Agent 与工具集成 |
| [通义千问](https://bailian.console.aliyun.com/) | 大语言模型 |
| [Gradio](https://gradio.app/) | Web 界面 |
| [SQLite](https://www.sqlite.org/) | 模拟业务数据库 |

##  数据说明

`shop.db` 由 `scripts/init_db.py` 自动生成，包含 6 张表（客户、商品、订单、订单明细、物流、售后工单），数据均为虚构。

##  License

MIT
