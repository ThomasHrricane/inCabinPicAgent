import os
import base64
import io
import json
from PIL import Image
from typing import Annotated, Union
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv

# ===== 配置 =====
load_dotenv()
api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL", "https://one-api.modelbest.co/v1")

SYSTEM_PROMPT = """你是一个智能助手，能够处理图片和文本信息。请根据用户提供的图片和文本内容进行回答。"""

MAX_MEMORY_ROUNDS = 0   # 只保留最开始 3 轮
OUTPUT_JSON_PATH = "./outputs/results_a3.json"
input_files = "my_corpus/a3.jsonl" # type: ignore

ContentType = list[Union[str, dict[str, Union[str, dict[str, str]]]]]

# ===== 初始化 LLM =====
llm = ChatOpenAI(
    api_key=api_key,  # type: ignore
    base_url=base_url,
    model="gemini-2.5-flash-nothinking",
    temperature=0.3,
    timeout=60,
    max_retries=3
)


class State(TypedDict):
    messages: Annotated[list, add_messages]
    memory_frozen: bool
    frozen_memory: list  # 保存冻结的前n轮对话


# ===== 对话节点 =====
def chatbot(state: State):
    system_msg = [m for m in state["messages"] if isinstance(m, SystemMessage)][-1]

    if not state["memory_frozen"]:
        # 还没冻结，正常传
        window = state["messages"]
        response = llm.invoke(window)

        new_messages = state["messages"] + [response]

        # 统计 human 数量，超过阈值时冻结
        human_count = sum(isinstance(m, HumanMessage) for m in new_messages)
        if human_count >= MAX_MEMORY_ROUNDS:
            # 冻结前三轮
            dialog = [m for m in new_messages if isinstance(m, (HumanMessage, AIMessage))]
            frozen_dialog = dialog[:MAX_MEMORY_ROUNDS * 2]  # 3轮 human + 3轮 ai
            state["frozen_memory"] = frozen_dialog
            state["memory_frozen"] = True

        return {"messages": new_messages, "memory_frozen": state["memory_frozen"], "frozen_memory": state["frozen_memory"]}

    else:
        # 记忆冻结后，只传 system + frozen_memory + 当前 human
        human_msg = [m for m in state["messages"] if isinstance(m, HumanMessage)][-1]
        window = [system_msg] + state["frozen_memory"] + [human_msg]

        response = llm.invoke(window)

        return {"messages": state["messages"] + [response], "memory_frozen": True, "frozen_memory": state["frozen_memory"]}



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

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

graph = graph_builder.compile()

# ===== 批量处理 =====
def batch_process(json_lines_path: str):
    # 初始状态：system + 未冻结
    state = {"messages": [SystemMessage(content=SYSTEM_PROMPT)], "memory_frozen": False, "frozen_memory": []}

    with open(json_lines_path, "r", encoding="utf-8") as f:
        lines = [json.loads(line.strip()) for line in f if line.strip()]

    results = []

    for idx, record in enumerate(lines, 1):
        try:
            source_text = record.get("source_text", "").strip()
            image_path = record.get("image_path", "").strip()

            message_content: ContentType = [{"type": "text", "text": source_text}]
            if os.path.exists(image_path):
                img_b64 = encode_image(image_path)
                message_content.append(
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                )
            else:
                print(f"第 {idx} 条数据找不到图片文件:{image_path}")

            # 新增一条 HumanMessage
            state["messages"].append(HumanMessage(content=message_content))  # type: ignore

            # 调用图
            state = graph.invoke(state)  # type: ignore

            # 取最新回复
            response_text = state["messages"][-1].content
            results.append({
                "index": idx,
                "image_path": image_path,
                "source_text": source_text,
                "response": response_text
            })

            # print(f"\n===== [第 {idx} 轮对话后] =====")
            # print(f"记忆是否冻结: {state['memory_frozen']}")
            # for i, message in enumerate(state["messages"]):
            #     role = "System" if isinstance(message, SystemMessage) else \
            #            "Human" if isinstance(message, HumanMessage) else \
            #            "AI" if isinstance(message, AIMessage) else "Unknown"
            #     preview = str(message.content)[:100].replace("\n", " ")
            #     print(f"  [{i+1}] {role}: {preview}...")
            # print("=" * 50 + "\n")

        except Exception as e:
            print(f"第 {idx} 条处理出错: {e}")

    save_results(results)


def save_results(data):
    if not data:
        return
    if os.path.exists(OUTPUT_JSON_PATH):
        with open(OUTPUT_JSON_PATH, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
    else:
        existing = []

    existing.extend(data)
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    batch_process(input_files)
