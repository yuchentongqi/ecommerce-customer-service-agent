# agent/graph.py
"""用 LangGraph 把各个节点串成客服工作流"""
from langgraph.graph import StateGraph, START, END

from agent.nodes import (
    AgentState,
    classify_intent,
    route_by_intent,
    sales_node,
    logistics_node,
    after_sales_node,
    chitchat_node,
    review_node,
)


def build_graph():
    builder = StateGraph(AgentState)

    # 注册节点
    builder.add_node("classify_intent", classify_intent)
    builder.add_node("sales", sales_node)
    builder.add_node("logistics", logistics_node)
    builder.add_node("after_sales", after_sales_node)
    builder.add_node("chitchat", chitchat_node)
    builder.add_node("review", review_node)

    # 入口
    builder.add_edge(START, "classify_intent")

    # 意图识别后，按意图路由到对应专业节点
    builder.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "售前": "sales",
            "物流": "logistics",
            "售后": "after_sales",
            "闲聊": "chitchat",
        },
    )

    # 每个专业节点处理完，都进入审核
    for node in ["sales", "logistics", "after_sales", "chitchat"]:
        builder.add_edge(node, "review")

    # 审核完成，结束
    builder.add_edge("review", END)

    return builder.compile()


if __name__ == "__main__":
    from langchain_core.messages import HumanMessage

    graph = build_graph()

    test_questions = [
        "你们那个无线蓝牙耳机多少钱？",
        "我的订单 1002 到哪了？",
        "订单 1005 我想退款，处理得怎么样了？",
        "你好呀",
    ]

    for q in test_questions:
        print("\n" + "=" * 50)
        print(f"用户：{q}")
        result = graph.invoke({
            "messages": [HumanMessage(content=q)],
            "intent": "",
            "answer": "",
            "review_passed": False,
        })
        print(f"意图：{result['intent']}")
        print(f"回复：{result['answer']}")