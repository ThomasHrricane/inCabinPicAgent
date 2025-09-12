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
import requests


def fill_standard_input(data, standard_template):
    """
    使用提供的数据填充standardInput模板中的tag_list。

    Args:
        data (dict): 包含车辆、人员、物品和宠物信息的字典。
        standard_template (dict): 包含完整结构的standardInput JSON模板。

    Returns:
        dict: 已填充好value的standardInput字典。
    """
    # 创建模板的深拷贝以避免修改原始模板
    output_json = json.loads(json.dumps(standard_template))

    # --- 辅助映射函数 ---
    def map_location(location_str):
        """
        根据规则转换位置名称，已适配新旧两种中排叫法。
        """
        if not location_str:
            return ["UNKNOWN"]
        mapping = {
            # 人员位置映射
            "前排左": "副驾",
            "前排右": "主驾",
            "中排左（若有）": "二排右",
            "中排右（若有）": "二排左",
            "中排左": "二排右", # 新增适配
            "中排右": "二排左", # 新增适配
            "后排左": "三排右",
            "后排右": "三排左",
            # 物品/宠物特定位置映射
            "中央扶手箱": "前排扶手箱",
            "中央扶手箱-杯槽": "前排扶手箱-杯槽",
        }
        return [mapping.get(location_str, "UNKNOWN")]
    
    def map_gender(gender_str):
        """确保性别数据能匹配模板中的枚举值。"""
        if not gender_str:
            return "UNKNOWN"
        mapping = {
            "女性": "女性",
            "女": "女性",
            "男性": "男性",
            "男": "男性"
        }
        return mapping.get(gender_str, "UNKNOWN")

    # 为了方便快速地更新value，创建一个从tag_key到tag对象的映射字典
    tag_list = output_json['label_result']['global']['100000'][0]['tag_list']
    tag_map = {tag['tag_key']: tag for tag in tag_list}

    # --- 1. 填充全局顶层信息 ---
    tag_map['是否抛弃']['value'] = '可用'
    tag_map['车内人数']['value'] = data.get('人', {}).get('人数', '0')
    tag_map['车内物品数']['value'] = data.get('物品', {}).get('物品数', '0')
    tag_map['车内宠物数']['value'] = data.get('宠物', {}).get('宠物数', '0')
    tag_map['晚上']['value'] = '晚上' if data.get('是否为黑夜') == '是' else '否'
    tag_map['摄像头位置']['value'] = '一排' if data.get('是否有中央扶手箱') == '是' else '二排'

    # --- 2. 填充人员详细信息 ---
    persons_data = data.get('人', {}).get('具体信息', [])
    for i, person in enumerate(persons_data):
        person_num = i + 1
        if f'person{person_num}-年龄' not in tag_map: continue # 防止数据超出模板定义范围

        tag_map[f'person{person_num}-年龄']['value'] = person.get('年龄', 'UNKNOWN')
        tag_map[f'person{person_num}-性别']['value'] = map_gender(person.get('性别'))
        tag_map[f'person{person_num}-位置']['value'] = map_location(person.get('位置'))
        tag_map[f'person{person_num}-行为']['value'] = [] # 行为按要求不填充
        
        # 着装1: 上衣样式 + 配饰
        clothing1_types = []
        if person.get('上衣样式'): clothing1_types.append(person['上衣样式'])
        if person.get('配饰'): clothing1_types.append(person['配饰'])
        tag_map[f'person{person_num}-衣裤-着装1类型']['value'] = clothing1_types
        
        # 着装1颜色: 上衣颜色 (处理逗号分隔的多个颜色)
        upper_colors = [color.strip() for color in person.get('上衣颜色', '').split(',') if color.strip()]
        tag_map[f'person{person_num}-衣裤-着装1颜色']['value'] = upper_colors
        
        # 着装2: 下装样式
        lower_style = person.get('下装样式')
        tag_map[f'person{person_num}-衣裤-着装2类型']['value'] = [lower_style] if lower_style else []
        
        # 着装2颜色: 下装颜色 (处理逗号分隔的多个颜色)
        lower_colors = [color.strip() for color in person.get('下装颜色', '').split(',') if color.strip()]
        tag_map[f'person{person_num}-衣裤-着装2颜色']['value'] = lower_colors

    # --- 3. 填充物品详细信息 ---
    items_data = data.get('物品', {}).get('具体信息', [])
    for i, item in enumerate(items_data):
        item_num = i + 1
        if f'good{item_num}-种类' not in tag_map: continue

        tag_map[f'good{item_num}-种类']['value'] = item.get('种类', 'UNKNOWN')
        tag_map[f'good{item_num}-位置']['value'] = map_location(item.get('位置'))

    # --- 4. 填充宠物详细信息 ---
    pets_data = data.get('宠物', {}).get('具体信息', [])
    for i, pet in enumerate(pets_data):
        pet_num = i + 1
        if f'pet{pet_num}-种类' not in tag_map: continue

        tag_map[f'pet{pet_num}-种类']['value'] = pet.get('种类', 'UNKNOWN')
        tag_map[f'pet{pet_num}-位置']['value'] = map_location(pet.get('位置'))
        
    return output_json





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




# ===== 图片转 Base64 =====
def encode_image(image_path: str, max_size=(2400, 1600)) -> str:
    with Image.open(image_path) as img:
        img = img.convert("RGB")
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    



def get_image_mime_type(image_bytes):
    """
    根据图片的前几个字节判断其MIME类型
    """
    if image_bytes.startswith(b'\xFF\xD8\xFF'):
        return 'image/jpeg'
    elif image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    elif image_bytes.startswith(b'GIF87a') or image_bytes.startswith(b'GIF89a'):
        return 'image/gif'
    elif image_bytes.startswith(b'RIFF') and image_bytes[8:12] == b'WEBP':
        return 'image/webp'
    else:
        return 'image/jpeg'  # 默认返回 JPEG

def image_url_to_base64_with_mime(image_url, max_size=(2400, 1600)):
    """
    获取图片，进行压缩和缩放处理，并返回包含正确MIME类型的Data URI
    """
    try:
        # 1. 从URL获取图片
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        # 2. 使用PIL打开图片并进行处理
        with Image.open(io.BytesIO(response.content)) as img:
            # 转换为RGB模式（移除Alpha通道）
            img = img.convert("RGB")
            # 如果图片尺寸超过最大尺寸，则进行缩放
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            # 将处理后的图片保存到内存缓冲区，格式为JPEG，质量为85
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            processed_image_bytes = buf.getvalue()

        # 3. 对处理后的图片进行Base64编码
        mime_type = 'image/jpeg'  # 因为我们强制保存为JPEG，所以MIME类型固定为image/jpeg
        base64_str = base64.b64encode(processed_image_bytes).decode('utf-8')

        return base64_str

    except Exception as e:
        print(f"操作失败: {e}")
        return None

# ===== 批量处理 =====
def batch_process(json_lines_path: str):
    # 初始状态：system + 未冻结
    state = {"messages": [SystemMessage(content=SYSTEM_PROMPT)], "memory_frozen": False, "frozen_memory": []}
    with open(json_lines_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    results = []
    for record in data:
        try:
            image_path = record.get("order_info")[1].get("value")
            message_content: ContentType = [{"type": "text", "text": ""}]
            
            img_b64 = image_url_to_base64_with_mime(image_path)
            message_content.append(
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}})
                

            # 新增一条 HumanMessage
            state["messages"].append(HumanMessage(content=message_content))  # type: ignore
            # 调用图
            state = graph.invoke(state)  # type: ignore
            # 取最新回复
            response_text = state["messages"][-1].content
            response_text = response_text.replace('\n', '').replace('```json', '').replace('```', '').strip()
            parsed_data = json.loads(response_text)
            final_result = fill_standard_input(parsed_data, record)
            # final_result = fill_standard_input(response_text, record)

            # recordSec = record.copy()
            # recordSec["tag_list"] = final_result

            results.append(final_result)
        except Exception as e:
            print(f"处理出错: {e}")
    return results
  


if __name__ == "__main__":
        
    # ===== 配置 =====
    load_dotenv()
    api_key = os.getenv("API_KEY")
    base_url = os.getenv("BASE_URL", "https://one-api.modelbest.co/v1")

    SYSTEM_PROMPT = "角色: 你是一位车内识别助手。\n任务: 严格按照json 格式,给出答案结果,答案均只能从备选项中选取并只选取一个,不要给出备选项中未出现的答案。以下为带有所有备选项的模版:\n{{\n    \"人\": {{\n        \"人数\": \"0,1,2,3,4,5,6\",\n        \"具体信息\": [\n            {{\n                \"性别\": \"男,女,unknown\",\n                \"位置\": \"前排左,前排右,中排左（若有）,中排右（若有）,后排左,后排右,过道,unknown\",\n                \"配饰\": \"眼镜,围巾,帽子,耳机,手表,墨镜,口罩,耳坠（非耳钉）,靴子,unknown\",\n                \"行为\": [\n                    {{\"是否在阅读\":\"是,否\"}},\n                    {{\"是否在化妆\":\"是,否\"}},\n                    {{\"是否在吃东西\":\"是,否\"}},\n                    {{\"是否在托腮思考\":\"是,否\"}},\n                    {{\"是否在玩手机\":\"是,否\"}},\n                    {{\"是否在打电话\":\"是,否\"}},\n                    {{\"是否在吸烟\":\"是,否\"}},\n                    {{\"是否在点烟\":\"是,否\"}},\n                    {{\"是否在睡觉\":\"是,否\"}},\n                    {{\"是否在抱猫\":\"是,否\"}},\n                    {{\"是否在抱狗\":\"是,否\"}},\n                    {{\"是否头或手伸出窗外\":\"是,否\"}},\n                    {{\"是否在哭闹\":\"是,否\"}},\n                    {{\"是否未系安全带\":\"是,否\"}},\n                    {{\"是否食指指向前\":\"是,否\"}},\n                    {{\"是否食指指向上\":\"是,否\"}},\n                    {{\"是否食指指向下\":\"是,否\"}},\n                    {{\"是否食指指向左\":\"是,否\"}},\n                    {{\"是否食指指向右\":\"是,否\"}},\n                    {{\"是否手触碰车顶屏幕\":\"是,否\"}},\n                    {{\"是否在站立\":\"是,否\"}}\n                ]\n            }}\n        ]\n    }}\n}}\n背景:\n- 目标: 根据给出的图片,将json 模版中各选择题选择出最合适的答案\n输出要求:\n- 一个个分析每个选项，对于行为中的每一项问题一步步来分析，尤其需要重视行为列表中的每一个选择，确保识别图片与思考完整后再给出每一个行为列表选择的答案\n- 选择的答案必须为该问题备选项中的项,如果不是则重新从备选项中选择\n- 以图片左侧为左,右侧为右。\n- 如有多个人,按照前排左、前排右、中排左（若有）、中排右（若有）、后排左、后排右 顺序展开\n- 若有两排座位,用前排、后排代称。若有三排座位,用前排、中排、后排代称,即此时第二排只能用中排代称。\n- 只输出json ,不要给出解释或说明\n- 人的具体信息列表这里要根据其人数来确定列表中应有几项字典并自动增加。\n- 结合常识判断各行为标签的共存是否可能,如一般情况下不会有人在阅读的同时在化妆,因此如果有此情况则将其改为否\n- 年龄14岁以下认为是儿童,能在车内站立也认为是儿童\n- 两排座位之间为过道,三排座位车非前排时,同一排两座位间也为过道\n\n格式: 输出为json\n- 避免:\n  1. 不要输出任何其他内容,只输出该json模版答案替换后的版本\n  2. 不要给出未知,可能是,不明,不知晓等所有表示不确定的词语,都用unknown代替\n  3. 衣服的样式答案不要给出多种可能,给出备选项中最可能的一种,完全无法确定就给unknown\n  4. 颜色的选择不要给出深绿、蓝绿这些,严格从备选项中进行选择\n- 示例 (输出参考):\n- 好的输出:\n{{\n\"人\": {{\n\"人数\": \"2\",\n\"具体信息\": [\n{{\n\"性别\": \"男\",\n\"位置\": \"前排右\",\n\"配饰\":\"眼镜,围巾\",\n\"行为\":[\n{{\"是否在阅读\":\"是,否\"}},\n{{\"是否在化妆\":\"否\"}},\n{{\"是否在吃东西\":\"否\"}},\n{{\"是否在托腮思考\":\"否\"}},\n{{\"是否在玩手机\":\"否\"}},\n{{\"是否在打电话\":\"否\"}},\n{{\"是否在吸烟\":\"否\"}},\n{{\"是否在点烟\":\"否\"}},\n{{\"是否在睡觉\":\"否\"}},\n{{\"是否在抱猫\":\"否\"}},\n{{\"是否在抱狗\":\"否\"}},\n{{\"是否头或手伸出窗外\":\"否\"}},\n{{\"是否在哭闹\":\"否\"}},\n{{\"是否未系安全带\":\"是\"}},\n{{\"是否食指指向前\":\"否\"}},\n{{\"是否食指指向上\":\"否\"}},\n{{\"是否食指指向下\":\"否\"}},\n{{\"是否食指指向左\":\"否\"}},\n{{\"是否食指指向右\":\"否\"}},\n{{\"是否手触碰车顶屏幕\":\"否\"}},\n{{\"是否在站立\":\"否\"}}\n]\n}},\n{{\n\"性别\": \"女\",\n\"位置\": \"后排右\",\n\"配饰\":\"手表,墨镜,口罩,围巾\",\n\"行为\":[\n{{\"是否在阅读\":\"是\"}},\n{{\"是否在化妆\":\"否\"}},\n{{\"是否在吃东西\":\"否\"}},\n{{\"是否在托腮思考\":\"否\"}},\n{{\"是否在玩手机\":\"否\"}},\n{{\"是否在打电话\":\"否\"}},\n{{\"是否在吸烟\":\"否\"}},\n{{\"是否在点烟\":\"否\"}},\n{{\"是否在睡觉\":\"否\"}},\n{{\"是否在抱猫\":\"否\"}},\n{{\"是否在抱狗\":\"否\"}},\n{{\"是否头或手伸出窗外\":\"否\"}},\n{{\"是否在哭闹\":\"否\"}},\n{{\"是否未系安全带\":\"是\"}},\n{{\"是否食指指向前\":\"否\"}},\n{{\"是否食指指向上\":\"否\"}},\n{{\"是否食指指向下\":\"否\"}},\n{{\"是否食指指向左\":\"否\"}},\n{{\"是否食指指向右\":\"否\"}},\n{{\"是否手触碰车顶屏幕\":\"否\"}},\n{{\"是否在站立\":\"否\"}}\n]\n}}\n]\n}}\n}}\n\n- 避免的输出:\n{{\n\"人\": {{\n\"人数\": \"一\",\n\"具体信息\": [{{\"性别\":\"未知\",\"位置\":\"车上\",\"配饰\":\"太阳镜,高跟靴子\",\n\"行为\":[\n{{\"是否在阅读\":\"是\"}},\n{{\"是否在化妆\":\"是\"}},\n{{\"是否在吃东西\":\"不清楚\"}},\n{{\"是否在托腮思考\":\"是\"}},\n{{\"是否在玩手机\":\"否\"}},\n{{\"是否在打电话\":\"否\"}},\n{{\"是否在吸烟\":\"是\"}},\n{{\"是否在点烟\":\"是\"}},\n{{\"是否在睡觉\":\"否\"}},\n{{\"是否在抱猫\":\"否\"}},\n{{\"是否在抱狗\":\"是\"}},\n{{\"是否头或手伸出窗外\":\"不确定\"}},\n{{\"是否在哭闹\":\"是\"}},\n{{\"是否未系安全带\":\"否\"}},\n{{\"是否食指指向前\":\"否\"}},\n{{\"是否食指指向上\":\"否\"}},\n{{\"是否食指指向下\":\"是\"}},\n{{\"是否食指指向左\":\"是\"}},\n{{\"是否食指指向右\":\"否\"}},\n{{\"是否手触碰车顶屏幕\":\"否\"}},\n{{\"是否在站立\":\"是\"}}\n]\n}}]\n}}\n}}\n"

    MAX_MEMORY_ROUNDS = 0   # 只保留最开始 3 轮
    # OUTPUT_JSON_PATH = "./outputs/results_a11.json"
    input_files = "./outputs/test21.json" # type: ignore

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
    graph_builder = StateGraph(State)
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_edge("chatbot", END)
    graph = graph_builder.compile()
    # standard_input_filepath = './outputs/test21.json'
    OUTPUT_JSON_PATH = './outputs/temp.json'
    try:
        # 从文件加载完整的JSON模板
        results = batch_process(input_files)

        # 以美化的格式将最终生成的完整JSON写入文件
        with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        
        print(f"处理成功！结果已保存至: {OUTPUT_JSON_PATH}")

    except FileNotFoundError as e:
        print(f"错误: 找不到文件 {e.filename}。请确保 'standardInput.json' 和 'data.json' 文件存在于脚本所在目录。")
    except json.JSONDecodeError:
        print("错误: JSON文件格式无效，请检查文件内容。")
    except Exception as e:
        print(f"发生未知错误: {e}")






    

