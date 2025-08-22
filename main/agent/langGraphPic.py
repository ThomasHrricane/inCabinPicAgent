


import os
import base64
import io
from PIL import Image
from typing import Annotated
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

# ===== 配置 =====
API_KEY = os.getenv("ONE_API_KEY", "")
BASE_URL = "https://one-api.modelbest.co/v1"
MODEL_NAME = "gemini-2.5-flash-nothinking"

llm = ChatOpenAI(
    api_key=API_KEY, # type: ignore
    base_url=BASE_URL,
    model=MODEL_NAME,
    temperature=0.3,
    timeout=60,
    max_retries=3
)

memory = MemorySaver()

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

# ===== 图片转 Base64 =====
def encode_image(image_path: str, max_size=(2400, 1600)) -> str:
    with Image.open(image_path) as img:
        img = img.convert("RGB")
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return base64.b64encode(buf.getvalue()).decode("utf-8")

# ===== 对话节点 =====
def chatbot(state: State):
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile(checkpointer=memory)

# ===== 交互循环 =====
def interactive_chat():
    config = {"configurable": {"thread_id": "1"}}
    print("💬 输入你的问题，或用 img:路径 发送图片（可在后面加描述）。输入 quit 退出。")

    while True:
        user_input = input("\n你: ").strip()
        if user_input.lower() in ["quit", "exit"]:
            print("👋 再见！")
            break

        message_content = []
        if user_input.startswith("img:"):
            parts = user_input.split(" ", 1)
            img_path = parts[0][4:].strip()
            if not os.path.exists(img_path):
                print("⚠️ 找不到图片文件！")
                continue
            img_b64 = encode_image(img_path)
            message_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
            })
            if len(parts) > 1:
                message_content.insert(0, {"type": "text", "text": parts[1]})
        else:
            message_content.append({"type": "text", "text": user_input})

        events = graph.stream(
            {"messages": [HumanMessage(content=message_content)]},
            config, # type: ignore
            stream_mode="values",
        )
        for event in events:
            event["messages"][-1].pretty_print()

if __name__ == "__main__":
    interactive_chat()
