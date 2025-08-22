import os
import base64
import io
import json
from PIL import Image
from typing import Annotated, Union
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
# ===== 配置 =====


load_dotenv()
api_key = os.getenv("API_KEY")

base_url = os.getenv("BASE_URL", "https://one-api.modelbest.co/v1")
SYSTEM_PROMPT = """你是一个智能助手，能够处理图片和文本信息。请根据用户提供的图片和文本内容进行回答。"""

# 记忆轮数限制（只保留最近 N 轮）
MAX_MEMORY_ROUNDS = 3
OUTPUT_JSON_PATH = "./results_a3.json"  # 保存输出的文件路径
BATCH_SIZE = 5  # 每批次处理的图片数
input_files = "./my_corpus/a3.jsonl"  # 输入的 JSON Lines 文件路径

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

# ===== 有记忆功能 =====
memory = MemorySaver()

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

def truncate_rounds(messages, rounds=3):
    # 取“最新的一条 System（如果有）”
    systems = [m for m in messages if isinstance(m, SystemMessage)]
    sys_latest = systems[-1:]  # 0或1条

    # 只看 Human/AI 的来回
    dialog = [m for m in messages if isinstance(m, (HumanMessage, AIMessage))]
    # 最近 N*2 条（Human+AI 成对），若有孤立一条也能覆盖
    keep = dialog[-rounds*2-1:]
    truncated_messages = sys_latest + keep

    # === 增强的打印输出 ===
    print("\n===== 截断后的对话 =====")
    print(f"本次模型参考的记忆 (最近 {rounds} 轮):")
    for i, message in enumerate(truncated_messages):
        role = "Unknown"
        content_preview = ""
        if isinstance(message, SystemMessage):
            role = "System"
        elif isinstance(message, HumanMessage):
            role = "Human"
            # 处理多模态内容
            if isinstance(message.content, list):
                text_parts = [part["text"] for part in message.content if part["type"] == "text"] # type: ignore
                image_parts = [part for part in message.content if part["type"] == "image_url"] # pyright: ignore[reportArgumentType]
                content_preview = "".join(text_parts)
                if image_parts:
                    content_preview += f" (+ {len(image_parts)} 张图片)"
            else:
                content_preview = str(message.content).strip()
        elif isinstance(message, AIMessage):
            role = "AI"
            content_preview = str(message.content).strip()

        # 为了终端输出整洁，只显示部分内容
        print(f"  [{i+1}] {role}: {content_preview[:150].replace(chr(10), ' ')}...") # type: ignore
    print("=" * 50 + "\n")
    # =====================

    return truncated_messages


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

    window = truncate_rounds(state["messages"], MAX_MEMORY_ROUNDS)
    response = llm.invoke(window)
    return {"messages": [response]}


graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile(checkpointer=memory)

# ===== 批量处理 =====
def batch_process(json_lines_path: str):
    # 为每个批处理任务设置一个唯一的线程ID
    config = {"configurable": {"thread_id": "batch_run_1"}}
    
    with open(json_lines_path, "r", encoding="utf-8") as f:
        lines = [json.loads(line.strip()) for line in f if line.strip()]

    results = []
    
    # 在处理第一条记录前，先向模型发送系统提示
    # 这确保系统提示只在首次被加入
    first_record = lines[0]
    first_content: ContentType = [
        {"type": "text", "text": first_record.get("source_text", "").strip()}
    ]
    if os.path.exists(first_record.get("image_path", "")):
        img_b64 = encode_image(first_record["image_path"])
        first_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}})
    
    # 首次调用，传入系统提示和第一个用户问题
    first_event = graph.invoke(
        {"messages": [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=first_content)]},
        config, # type: ignore
    )
    # 处理首次调用结果
    response_text = first_event["messages"][-1].content
    results.append({
        "index": 1,
        "image_path": first_record.get("image_path", ""),
        "source_text": first_record.get("source_text", ""),
        "response": response_text
    })




    print(f"\n===== [完整对话历史] - 第 {1} 轮 =====")
    print("完整记忆:")
    for i, message in enumerate(first_event["messages"]):
        # 再次实现你的打印逻辑
        role = "Unknown"
        if isinstance(message, SystemMessage): role = "System"
        elif isinstance(message, HumanMessage): role = "Human"
        elif isinstance(message, AIMessage): role = "AI"
        content_preview = str(message.content).strip()
        print(f"  [{i+1}] {role}: {content_preview[:150].replace(chr(10), ' ')}...")
    print("=" * 50 + "\n")






    # 从第二条记录开始，只传入当前 HumanMessage
    for idx, record in enumerate(lines[1:], 2): # 从索引 2 开始
        try:
            source_text = record.get("source_text", "").strip()
            image_path = record.get("image_path", "").strip()
            
            message_content: ContentType = [{"type": "text", "text": source_text}]
            if os.path.exists(image_path):
                img_b64 = encode_image(image_path)
                message_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}})
            else:
                print(f"第 {idx} 条数据找不到图片文件:{image_path}")

            # 每次循环只传入一个 HumanMessage，langgraph 会自动处理记忆
            events = graph.stream(
                {"messages": [HumanMessage(content=message_content)]},
                config, # type: ignore
                stream_mode="values",
            )
            
            last_event = None
            for event in events:
                last_event = event
            

            current_state = graph.get_state(config) # type: ignore
            full_messages = current_state.values["messages"]
            print(f"实际保存的消息总数: {len(full_messages)}")
            





            print(f"\n===== [完整对话历史] - 第 {len(full_messages) // 2} 轮 =====")
            print("完整记忆:")
            for i, message in enumerate(full_messages):
                # 再次实现你的打印逻辑
                role = "Unknown"
                if isinstance(message, SystemMessage): role = "System"
                elif isinstance(message, HumanMessage): role = "Human"
                elif isinstance(message, AIMessage): role = "AI"
                content_preview = str(message.content).strip()
                print(f"  [{i+1}] {role}: {content_preview[:150].replace(chr(10), ' ')}...")
            print("=" * 50 + "\n")






            if last_event and "messages" in last_event:
                response_text = last_event["messages"][-1].content
                results.append({
                    "index": idx,
                    "image_path": image_path,
                    "source_text": source_text,
                    "response": response_text
                })

        except Exception as e:
            print(f"第 {idx} 条处理出错: {e}")
            
    # 最后保存所有结果
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
    print(data)
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    batch_process(input_files)
