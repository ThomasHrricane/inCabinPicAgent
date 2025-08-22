import streamlit as st
from openai import OpenAI
import time
import base64
from io import BytesIO
from PIL import Image

# --- 1. 页面和模型配置 ---

# 页面配置
st.set_page_config(
    page_title="AI模型对话服务",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS样式 (与原版相同)
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stTextArea textarea {
        height: 150px;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
    }
    .chat-message.user {
        background-color: #e6f3ff;
    }
    .chat-message.assistant {
        background-color: #f0f0f0;
    }
    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        margin-right: 1rem;
    }
    .message {
        flex: 1;
    }
</style>
""", unsafe_allow_html=True)

# 【新】支持的豆包模型列表 (方便管理)
DOUBAO_MODELS = {
    # 显示在下拉菜单中的名字 : 实际API调用的模型ID
    "doubao-1-5-vision-pro-32k-250115": "doubao-1-5-vision-pro-32k-250115",
    "doubao-1.5-vision-pro-250328": "doubao-1.5-vision-pro-250328",
    "doubao-1.5-vision-lite-250315": "doubao-1.5-vision-lite-250315"
}

# 支持的 One-API 模型列表
ONE_API_MODELS = [
    "claude-3-5-sonnet-20241022",
    "claude-3-7-sonnet-20250219",
    "claude-3-7-sonnet-20250219-official",
    "claude-3-7-sonnet-20250219-thinking",
    "claude-sonnet-4-20250514",
    "claude-sonnet-4-20250514-thinking",
    "deepseek-chat",
    "deepseek-chat-0324",
    "deepseek-chat-official",
    "deepseek-reasoner",
    "deepseek-reasoner-0528",
    "deepseek-reasoner-official",
    "gemini-2.5-flash-preview-04-17-nothinking",
    "gemini-2.5-flash-preview-05-20",
    "gemini-2.5-flash-preview-05-20-nothinking",
    "gemini-2.5-flash-preview-05-20-thinking",
    "gemini-2.5-pro-exp-03-25",
    "gemini-2.5-pro-preview-05-06",
    "gemini-2.5-pro-preview-06-05",
    "gpt-4-turbo",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "gpt-4o",
    "gpt-4o-mini"
]

# 【新】合并所有模型用于下拉选择
ALL_MODELS = list(DOUBAO_MODELS.keys()) + ONE_API_MODELS


# --- 2. 初始化会话状态 ---

if "messages" not in st.session_state:
    st.session_state.messages = []

# 【新】分离两个API Key
if "one_api_key" not in st.session_state:
    st.session_state.one_api_key = ""
if "ark_api_key" not in st.session_state:
    st.session_state.ark_api_key = ""

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None


# --- 3. 辅助函数 ---

def image_to_base64(image):
    """将图片转换为base64编码"""
    buffered = BytesIO()
    # 确保图片是RGB模式，以兼容JPG等格式
    image.convert("RGB").save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


# --- 4. 侧边栏UI ---

with st.sidebar:
    st.title("🤖 AI模型对话服务")

    # 【新】API设置区域，分离了两个Key
    st.header("API设置")
    st.info("请根据选择的模型，填写对应的API密钥。")

    one_api_key = st.text_input(
        "One-API 密钥",
        type="password",
        value=st.session_state.one_api_key,
        help="用于 DeepSeek, Gemini, GPT 等模型"
    )
    if one_api_key:
        st.session_state.one_api_key = one_api_key

    ark_api_key = st.text_input(
        "火山方舟 (Doubao) API Key",
        type="password",
        value=st.session_state.ark_api_key,
        help="用于 doubao-vision-pro 等豆包模型"
    )
    if ark_api_key:
        st.session_state.ark_api_key = ark_api_key

    # 模型选择
    st.header("模型选择")
    selected_model = st.selectbox("选择模型", ALL_MODELS)

    # 参数设置
    st.header("参数设置")
    temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=0.7, step=0.1)
    max_tokens = st.slider("最大输出长度", min_value=100, max_value=4000, value=1000, step=100)

    # 清空对话
    if st.button("清空对话历史"):
        st.session_state.messages = []
        st.session_state.uploaded_image = None
        st.success("对话历史已清空！")

    # 关于信息
    st.markdown("---")
    st.markdown("支持 [One-API](https://one-api.modelbest.co) 和 [火山方舟](https://www.volcengine.com/product/ark) 服务")


# --- 5. 主界面 ---

st.title("AI模型对话")

# 显示对话历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "content" in message and isinstance(message["content"], list):
            for content_item in message["content"]:
                if content_item.get("type") == "text":
                    st.markdown(content_item.get("text", ""))
                elif content_item.get("type") == "image_url":
                    # 注意：st.image可以直接处理base64字符串
                    st.image(content_item.get("image_url", {}).get("url", ""))
        else:
            st.markdown(message.get("content", ""))

# 图片上传区域 (只在选择了视觉模型时显示)
# 【新】增强：只有视觉模型才提示上传图片
vision_models = list(DOUBAO_MODELS.keys()) # 未来可以加入更多视觉模型
if selected_model in vision_models:
    uploaded_file = st.file_uploader("上传图片（可选）", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.session_state.uploaded_image = Image.open(uploaded_file)
        st.image(st.session_state.uploaded_image, caption="已上传图片", width=300)
else:
    st.session_state.uploaded_image = None # 如果切换到非视觉模型，清除已上传图片


# 用户输入区域
user_input = st.chat_input("请输入您的问题...")

# --- 6. 核心逻辑：处理用户输入 ---

if user_input:
    # 准备用户消息
    user_message = {"role": "user", "content": user_input} # 默认文本消息

    # 如果有图片，构建多模态消息
    if st.session_state.uploaded_image is not None:
        image = st.session_state.uploaded_image
        image_base64 = image_to_base64(image)
        image_url = f"data:image/png;base64,{image_base64}"
        
        user_message["content"] = [ # type: ignore
            {"type": "text", "text": user_input},
            {"type": "image_url", "image_url": {"url": image_url}}
        ]
        
        # 显示用户消息（带图片）
        with st.chat_message("user"):
            st.markdown(user_input)
            st.image(image)
        
        # 使用后清除图片，避免重复使用
        st.session_state.uploaded_image = None
    else:
        # 显示用户消息（纯文本）
        with st.chat_message("user"):
            st.markdown(user_input)

    st.session_state.messages.append(user_message)

    # 显示助手正在输入的状态
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("思考中...")

        # 【新】核心改动：根据选择的模型，动态设置API参数
        client = None
        api_key_to_use = None
        base_url_to_use = None
        model_to_call = selected_model

        try:
            # 判断模型类型
            if selected_model in DOUBAO_MODELS:
                # --- A. 使用火山方舟（豆包）配置 ---
                if not st.session_state.ark_api_key:
                    st.error("请先在侧边栏设置火山方舟的API密钥！")
                    st.stop()
                
                api_key_to_use = st.session_state.ark_api_key
                base_url_to_use = "https://ark.cn-beijing.volces.com/api/v3"
                model_to_call = DOUBAO_MODELS[selected_model] # 获取真实的模型ID

            else:
                # --- B. 使用 One-API 配置 ---
                if not st.session_state.one_api_key:
                    st.error("请先在侧边栏设置 One-API 的密钥！")
                    st.stop()

                api_key_to_use = st.session_state.one_api_key
                base_url_to_use = "https://one-api.modelbest.co/v1"
                # model_to_call 已经是正确的了

            # 创建OpenAI客户端
            client = OpenAI(
                api_key=api_key_to_use,
                base_url=base_url_to_use
            )

            # 发送请求
            response = client.chat.completions.create(
                model=model_to_call,
                messages=st.session_state.messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # 获取并显示回复
            assistant_response = response.choices[0].message.content
            message_placeholder.markdown(assistant_response)

            # 添加助手回复到历史
            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_response
            })

        except Exception as e:
            error_message = f"请求出错: {str(e)}"
            message_placeholder.error(error_message)
