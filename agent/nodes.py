# agent/nodes.py
"""Agent 各节点：意图识别、专业客服、回复审核"""
import os
from typing import Annotated, TypedDict
from operator import add

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from agent.tools import (
    query_product, query_order, query_logistics,
    query_after_sales, query_customer_orders,
)

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "qwen3.7-flash")
BASE_URL = os.getenv("BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
API_KEY = os.getenv("DASHSCOPE_API_KEY")


def get_llm():
    return ChatOpenAI(
        model=MODEL_NAME,
        api_key=API_KEY,
        base_url=BASE_URL,
        temperature=0,
    )


# ============ 状态 ============
class AgentState(TypedDict):
    messages: Annotated[list, add]
    intent: str
    answer: str
    review_passed: bool


# ============ 意图识别 ============
INTENT_PROMPT = """你是电商客服的意图分类器。判断用户问题属于哪一类，只返回一个词：

- 售前：询问商品信息、价格、库存、推荐
- 物流：询问订单状态、物流进度、发货情况
- 售后：退款、退货、换货、投诉
- 闲聊：打招呼、闲聊、无明确业务需求

用户问题：{question}

只返回：售前 / 物流 / 售后 / 闲聊"""


def classify_intent(state: AgentState):
    question = state["messages"][-1].content
    llm = get_llm()
    result = llm.invoke([HumanMessage(content=INTENT_PROMPT.format(question=question))])
    raw = result.content.strip()

    # 兜底：从返回值里匹配有效的意图
    intent = "闲聊"
    for valid in ["售前", "物流", "售后", "闲聊"]:
        if valid in raw:
            intent = valid
            break

    print(f"[意图识别] {intent}")
    return {"intent": intent}


def route_by_intent(state: AgentState):
    """根据意图路由到对应节点"""
    return state["intent"]


# ============ 售前 Agent ============
_SALES_AGENT = None


def get_sales_agent():
    global _SALES_AGENT
    if _SALES_AGENT is None:
        _SALES_AGENT = create_react_agent(
            get_llm(),
            tools=[query_product],
            prompt="你是电商售前客服。用户询问商品价格、库存、推荐时，调用工具查询后回答。只根据工具返回的信息作答，不要编造。回复简洁友好，150字以内。",
        )
    return _SALES_AGENT


def sales_node(state: AgentState):
    agent = get_sales_agent()
    result = agent.invoke({"messages": state["messages"]})
    return {"answer": result["messages"][-1].content}


# ============ 物流 Agent ============
_LOGISTICS_AGENT = None


def get_logistics_agent():
    global _LOGISTICS_AGENT
    if _LOGISTICS_AGENT is None:
        _LOGISTICS_AGENT = create_react_agent(
            get_llm(),
            tools=[query_order, query_logistics, query_customer_orders],
            prompt="你是电商物流客服。用户询问订单状态或物流进度时，调用工具查询后回答。如果用户没提供订单号，请礼貌询问。只根据工具返回的信息作答，不要编造。",
        )
    return _LOGISTICS_AGENT


def logistics_node(state: AgentState):
    agent = get_logistics_agent()
    result = agent.invoke({"messages": state["messages"]})
    return {"answer": result["messages"][-1].content}


# ============ 售后 Agent ============
_AFTER_SALES_AGENT = None


def get_after_sales_agent():
    global _AFTER_SALES_AGENT
    if _AFTER_SALES_AGENT is None:
        _AFTER_SALES_AGENT = create_react_agent(
            get_llm(),
            tools=[query_order, query_after_sales, query_customer_orders],
            prompt="你是电商售后客服。用户咨询退款、退货、换货、投诉时，调用工具查询订单和售后记录后回答。只根据工具返回的信息作答，不要编造。",
        )
    return _AFTER_SALES_AGENT


def after_sales_node(state: AgentState):
    agent = get_after_sales_agent()
    result = agent.invoke({"messages": state["messages"]})
    return {"answer": result["messages"][-1].content}


# ============ 闲聊 ============
def chitchat_node(state: AgentState):
    llm = get_llm()
    question = state["messages"][-1].content
    result = llm.invoke([
        SystemMessage(content="你是友好的电商客服助手。简短回复用户的打招呼或闲聊，并引导他们提出具体需求（查商品、查物流、查售后）。"),
        HumanMessage(content=question),
    ])
    return {"answer": result.content}


# ============ 回复审核 ============
REVIEW_PROMPT = """你是回复审核员。检查下面的客服回复是否有严重问题：

用户问题：{question}
客服回复：{answer}

只在出现以下**明确问题**时才判不通过：
1. 编造了与事实明显矛盾的信息（例如把已知的"运输中"说成"已签收"）
2. 做出了不恰当的承诺（例如"保证明天送达"、"百分百退款"）
3. 答非所问，完全没回应用户的问题

注意：客服回复中的具体数字（价格、库存、订单状态）通常来自后台工具查询，**不要仅因为出现具体数字就判为编造**。

如果回复没有上述问题，只返回：通过
如果有问题，返回：不通过 | 原因

只返回一行，不要其他内容。"""


def review_node(state: AgentState):
    question = state["messages"][-1].content
    answer = state["answer"]

    llm = get_llm()
    result = llm.invoke([
        HumanMessage(content=REVIEW_PROMPT.format(question=question, answer=answer))
    ])
    verdict = result.content.strip()

    passed = verdict.startswith("通过")
    print(f"[审核] {'通过' if passed else verdict[:60]}")

    return {
        "review_passed": passed,
        "messages": [AIMessage(content=answer)],
    }