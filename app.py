# app.py
import gradio as gr
from langchain_core.messages import HumanMessage

from agent.graph import build_graph

print("正在初始化客服 Agent...")
graph = build_graph()
print("Agent 就绪")

# 保存最近一次的意图，方便界面展示
last_state = {"intent": ""}


def respond(message, chat_history):
    if not message.strip():
        return "", chat_history, last_state["intent"]

    result = graph.invoke({
        "messages": [HumanMessage(content=message)],
        "intent": "",
        "answer": "",
        "review_passed": False,
    })

    answer = result["answer"]
    intent = result["intent"]
    last_state["intent"] = intent

    chat_history = chat_history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": answer},
    ]
    return "", chat_history, intent


with gr.Blocks(title="电商客服 Agent") as demo:
    gr.Markdown("# 电商客服 Agent")
    gr.Markdown("多 Agent 协作：意图识别 → 专业客服 → 回复审核")

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=450, label="对话")
            msg = gr.Textbox(
                placeholder="输入问题，按回车发送...",
                label="你的问题",
                lines=1,
            )
            with gr.Row():
                send_btn = gr.Button("发送", variant="primary")
                clear_btn = gr.Button("清空")

        with gr.Column(scale=1):
            gr.Markdown("### 意图识别")
            intent_box = gr.Textbox(label="当前意图", interactive=False)

            gr.Markdown("### 试试这些问题")
            gr.Examples(
                examples=[
                    "无线蓝牙耳机多少钱？",
                    "我的订单 1002 到哪了？",
                    "订单 1005 退款处理得怎么样了？",
                    "你好呀",
                ],
                inputs=msg,
            )

    msg.submit(respond, [msg, chatbot], [msg, chatbot, intent_box])
    send_btn.click(respond, [msg, chatbot], [msg, chatbot, intent_box])
    clear_btn.click(lambda: (None, "", ""), None, [chatbot, intent_box, msg])


if __name__ == "__main__":
    demo.launch()