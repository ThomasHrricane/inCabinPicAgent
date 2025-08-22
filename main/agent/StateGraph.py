# import os
# import json
# import base64
# import mimetypes
# import io
# import uuid
# from typing import Annotated, Union, List, Dict, Any, Optional
# from typing_extensions import TypedDict
# from pathlib import Path
# from PIL import Image
# from langgraph.graph import StateGraph, START, END
# from langgraph.graph.message import add_messages
# from langgraph.prebuilt import ToolNode, tools_condition
# from langgraph.checkpoint.memory import MemorySaver
# from langgraph.types import Command, interrupt
# from langchain_core.messages import BaseMessage, ToolMessage, HumanMessage, AIMessage
# from langchain_core.runnables import RunnableConfig
# from langchain_core.tools import tool
# from langchain.chat_models import init_chat_model
# from langchain_tavily import TavilySearch




# os.environ["OPENAI_API_KEY"] = "sk-Rdhp0NuPVXwwsp0z0c276e1024C84dF0A22dB85bBb2bE4Fd"
# os.environ["OPENAI_API_BASE"] = "https://one-api.modelbest.co/v1"
# os.environ["TAVILY_API_KEY"] = ""


# # 修复类型定义
# MessageContent = Union[
#     Dict[str, str],  # 文本内容: {"type": "text", "text": "..."}
#     Dict[str, Union[str, Dict[str, str]]]  # 图片内容: {"type": "image_url", "image_url": {...}}
# ]

# # 初始化内存和LLM
# memory = MemorySaver()
# llm = init_chat_model("gemini-2.5-flash-preview-05-20-nothinking")

# class State(TypedDict):
#     messages: Annotated[list, add_messages]

# graph_builder = StateGraph(State)

# # 图片处理工具
# @tool
# def image_analysis(description: str) -> str:
#     """Analyze image content based on user's description or question about the image."""
#     return f"Image analysis requested: {description}"

# # 定义人工协助工具
# @tool
# def human_assistance(query: str) -> str:
#     """Request assistance from a human."""
#     human_response = interrupt({"query": query})
#     return human_response["data"]

# # 定义搜索工具
# @tool
# def web_search(query: str) -> str:
#     """Perform a web search for the given query."""
#     return f"搜索结果：根据查询 '{query}'，找到了相关信息。（这是模拟搜索结果）"

# # 工具列表
# tools = [human_assistance, web_search, image_analysis]
# llm_with_tools = llm.bind_tools(tools)

# def chatbot(state: State):
#     return {"messages": [llm_with_tools.invoke(state["messages"])]}

# # 添加节点
# graph_builder.add_node("chatbot", chatbot)
# tool_node = ToolNode(tools=tools)
# graph_builder.add_node("tools", tool_node)

# # 添加边
# graph_builder.add_conditional_edges("chatbot", tools_condition)
# graph_builder.add_edge("tools", "chatbot")
# graph_builder.add_edge(START, "chatbot")

# # 编译图
# graph = graph_builder.compile(checkpointer=memory)

# def create_text_message(text: str) -> HumanMessage:
#     """创建纯文本消息"""
#     return HumanMessage(content=text)

# def create_image_message_safe(text: str, image_path: Optional[str] = None, image_url: Optional[str] = None) -> HumanMessage:
#     """安全地创建包含图片的消息"""
#     content: List[MessageContent] = []

#     # 添加文本内容
#     if text:
#         text_content: MessageContent = {"type": "text", "text": text}
#         content.append(text_content)

#     if image_url:
#         # 对于网络图片，直接使用URL
#         image_content: MessageContent = {
#             "type": "image_url",
#             "image_url": {
#                 "url": image_url,
#                 "detail": "auto"
#             }
#         }
#         content.append(image_content)

#     elif image_path:
#         try:
#             # 对于本地图片，进行安全处理
#             path = Path(image_path)
#             if path.exists() and path.stat().st_size > 0:
#                 # 使用PIL重新处理图片确保格式正确
#                 with Image.open(path) as img:
#                     # 转换为RGB并压缩
#                     if img.mode in ('RGBA', 'LA', 'P'):
#                         img = img.convert('RGB')

#                     # 调整大小以减少token使用
#                     img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)

#                     # 保存到内存
#                     img_buffer = io.BytesIO()
#                     img.save(img_buffer, format='JPEG', quality=80, optimize=True)
#                     img_buffer.seek(0)

#                     # 编码为base64
#                     base64_string = base64.b64encode(img_buffer.read()).decode('utf-8')

#                     # 验证编码结果
#                     try:
#                         base64.b64decode(base64_string)
#                         image_content: MessageContent = {
#                             "type": "image_url",
#                             "image_url": {
#                                 "url": f"data:image/jpeg;base64,{base64_string}",
#                                 "detail": "auto"
#                             }
#                         }
#                         content.append(image_content)
#                     except Exception as e:
#                         error_content: MessageContent = {"type": "text", "text": f"图片处理失败: {str(e)}"}
#                         content.append(error_content)
#             else:
#                 error_content: MessageContent = {"type": "text", "text": f"图片文件无效: {image_path}"}
#                 content.append(error_content)
#         except Exception as e:
#             error_content: MessageContent = {"type": "text", "text": f"图片处理错误: {str(e)}"}
#             content.append(error_content)

#     return HumanMessage(content=content) # type: ignore

# def run_conversation_safe(message: str, config: RunnableConfig, image_path: Optional[str] = None, image_url: Optional[str] = None, max_retries: int = 3):
#     """安全地运行对话，包含重试机制"""
#     print("=== 用户输入 ===")
#     print(f"文本: {message}")
#     if image_path:
#         print(f"图片路径: {image_path}")
#     if image_url:
#         print(f"图片URL: {image_url}")
#     print("\n=== AI 响应 ===")

#     for attempt in range(max_retries):
#         try:
#             # 创建消息
#             if image_path or image_url:
#                 user_message = create_image_message_safe(message, image_path, image_url)
#             else:
#                 user_message = create_text_message(message)

#             # 流式处理对话
#             events = graph.stream(
#                 {"messages": [user_message]},
#                 config,
#                 stream_mode="values",
#             )

#             for event in events:
#                 if "messages" in event:
#                     event["messages"][-1].pretty_print()

#             return  # 成功执行，退出函数

#         except Exception as e:
#             print(f"尝试 {attempt + 1} 失败: {str(e)}")
#             if attempt < max_retries - 1:
#                 print("重试中...")
#                 # 如果是历史数据问题，尝试使用新的thread_id
#                 if "base64" in str(e) or "decode" in str(e):
#                     config["configurable"]["thread_id"] = str(uuid.uuid4()) # type: ignore
#                     print(f"使用新的thread_id: {config['configurable']['thread_id']}") # type: ignore
#             else:
#                 print("所有重试都失败了")

# def start_fresh_conversation() -> RunnableConfig:
#     """开始一个全新的对话会话"""
#     config: RunnableConfig = {"configurable": {"thread_id": str(uuid.uuid4())}}
#     print(f"开始新对话，thread_id: {config['configurable']['thread_id']}")
#     return config

# def run_text_only_test():
#     """只运行文本对话测试"""
#     print("=== 纯文本对话测试 ===")
#     config = start_fresh_conversation()

#     # 测试简单对话
#     test_messages = [
#         "你好！",
#         "什么是人工智能？",
#         "你能搜索一些信息吗？搜索关键词：机器学习",
#         "你还记得我问的第一个问题吗？"
#     ]

#     for i, msg in enumerate(test_messages, 1):
#         print(f"\n--- 测试 {i} ---")
#         run_conversation_safe(msg, config)
#         print()

# def run_image_test():
#     """运行图片测试"""
#     print("=== 图片处理测试 ===")
#     config = start_fresh_conversation()

#     # 测试网络图片
#     print("--- 图片测试 ---")
#     test_image_url = "C:/Users/ModelBest/Desktop/pre_test_data/2.jpg"
#     run_conversation_safe(
#         "请描述这张图片的内容", 
#         config, 
#         image_url=test_image_url
#     )

# def test_simple_conversation():
#     """简单对话测试"""
#     print("=== 简单对话测试 ===")
#     config = start_fresh_conversation()

#     # 最简单的测试
#     run_conversation_safe("你好，介绍一下你自己", config)

# # 主程序
# if __name__ == "__main__":
#     try:
#         # 从最简单的测试开始
#         test_simple_conversation()

#         print("\n" + "="*60 + "\n")

#         # 然后测试更复杂的功能
#         run_text_only_test()

#         print("\n" + "="*60 + "\n")

#         # 最后测试图片功能
#         run_image_test()

#     except Exception as e:
#         print(f"程序执行出错: {e}")
#         print("请检查网络连接和API配置")

# # 额外的工具函数
# def clear_conversation_history():
#     """清除对话历史"""
#     global memory
#     memory = MemorySaver()
#     global graph
#     graph = graph_builder.compile(checkpointer=memory)
#     print("对话历史已清除")

# def test_api_connection() -> bool:
#     """测试API连接"""
#     try:
#         # 创建一个简单的测试
#         test_llm = init_chat_model("gpt-4o")
#         response = test_llm.invoke([HumanMessage(content="Hello")])
#         print("API连接正常")
#         return True
#     except Exception as e:
#         print(f"API连接失败: {e}")
#         return False

# # 简化版本 - 如果类型问题仍然存在
# def create_simple_message(text: str) -> HumanMessage:
#     """创建简单文本消息（绕过类型检查问题）"""
#     return HumanMessage(content=[{"type": "text", "text": text}])

# def create_simple_image_message(text: str, image_url: str) -> HumanMessage:
#     """创建简单的图片消息（绕过类型检查问题）"""
#     content = [
#         {"type": "text", "text": text},
#         {
#             "type": "image_url", 
#             "image_url": {"url": image_url, "detail": "auto"}
#         }
#     ]
#     return HumanMessage(content=content)





# # config: RunnableConfig = {"configurable": {"thread_id": "1"}}

# # events = graph.stream(
# #     {"messages": [HumanMessage(content="Hi! My name is Will.")]},
# #     config,
# #     stream_mode="values",
# # )
# # for event in events:
# #     event["messages"][-1].pretty_print()

# # print("\n--- 第二轮 ---\n")

# # # 第二次：同样的 thread_id，再问它名字
# # events = graph.stream(
# #     {"messages": [HumanMessage(content="What's my name?")]},
# #     config,  # 同一个 thread_id
# #     stream_mode="values",
# # )
# # for event in events:
# #     event["messages"][-1].pretty_print()






















# # class State(TypedDict):
# #     messages: Annotated[list, add_messages]

# # def chatbot(state: State):
# #     return {"messages": [llm_with_tools.invoke(state["messages"])]}

# # # 将 BasicToolNode 转换为函数形式
# # def tool_node(state: State):
# #     """执行工具调用的节点函数"""
# #     if not state.get("messages"):
# #         raise ValueError("No messages found in input")

# #     message = state["messages"][-1]
# #     outputs = []
# #     tools_by_name = {tool.name: tool for tool in tools}

# #     if hasattr(message, "tool_calls"):
# #         for tool_call in message.tool_calls:
# #             tool_result = tools_by_name[tool_call["name"]].invoke(
# #                 tool_call["args"]
# #             )
# #             outputs.append(
# #                 ToolMessage(
# #                     content=json.dumps(tool_result),
# #                     name=tool_call["name"],
# #                     tool_call_id=tool_call["id"],
# #                 )
# #             )

# #     return {"messages": outputs}

# # def route_tools(state: State):
# #     """
# #     根据最后一条消息是否有工具调用来路由到不同节点
# #     """
# #     if not state.get("messages"):
# #         return END

# #     message = state["messages"][-1]
# #     if hasattr(message, "tool_calls") and message.tool_calls:
# #         return "tools"
# #     return END

# # 初始化工具和模型
# # tool = TavilySearch(max_results=2)
# # tools = [tool]
# # llm = init_chat_model("gpt-4o")
# # llm_with_tools = llm.bind_tools(tools)

# # # 构建图
# # graph_builder = StateGraph(State)
# # graph_builder.add_node("chatbot", chatbot)
# # graph_builder.add_node("tools", tool_node)  # 使用函数形式的工具节点

# # # 添加条件边
# # graph_builder.add_conditional_edges(
# #     "chatbot",
# #     route_tools,
# #     {"tools": "tools", END: END},
# # )

# # # 添加其他边
# # graph_builder.add_edge("tools", "chatbot")
# # graph_builder.add_edge(START, "chatbot")

# # # 编译图
# # graph = graph_builder.compile()









from typing import Annotated
from langchain_openai.chat_models import ChatOpenAI  # 使用 ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

import os

# --- 配置 ---
# 你可以通过环境变量设置，或直接写在这里
API_KEY = os.getenv("ONE_API_KEY", "sk-QXBk42qBjv5bsT4PC3B72021FeDc4bA28f4b2bDdFe8aA8C3")  # 替换为你的实际 Key
BASE_URL = "https://one-api.modelbest.co/v1"  # 第三方代理地址
MODEL_NAME = "gemini-2.5-flash-nothinking"  # 确保代理支持此模型名

# 初始化模型（指向代理）
llm = ChatOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    model=MODEL_NAME,
    temperature=0.3,
    timeout=30,
    max_retries=3
)


class State(TypedDict):
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)


def chatbot(state: State):
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()


def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [HumanMessage(content=user_input)]}):
        for value in event.values():
            if isinstance(value, dict) and "messages" in value:
                message = value["messages"][-1]
                if isinstance(message, AIMessage):
                    print("Assistant:", message.content)


# 交互循环
while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        stream_graph_updates(user_input)
    except KeyboardInterrupt:
        print("\nGoodbye!")
        break
    except Exception as e:
        print(f"Error: {e}")
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        stream_graph_updates(user_input)
        break



