import json
import os



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


# --- 主程序执行 ---
if __name__ == "__main__":
    # 定义输入和输出文件路径
    # template = "./outputs/template.json"
    standard_input_filepath = './outputs/test21.json'
    data_filepath = './outputs/test_data.json'
    output_directory = 'outputs'
    output_filepath = os.path.join(output_directory, 'filled_output.json')

    # 确保输出目录存在
    os.makedirs(output_directory, exist_ok=True)
    
    try:
        # 从文件加载完整的JSON模板
        with open(standard_input_filepath, 'r', encoding='utf-8') as f:
            full_standardInput_template = json.load(f)
        
        # 从文件加载要嵌入的数据
        with open(data_filepath, 'r', encoding='utf-8') as f:
            data_to_embed = json.load(f)

        # 调用函数处理数据
        final_result = fill_standard_input(data_to_embed, full_standardInput_template)

        # 以美化的格式将最终生成的完整JSON写入文件
        with open(output_filepath, "w", encoding="utf-8") as f:
            json.dump(final_result, f, ensure_ascii=False, indent=4)
        
        print(f"处理成功！结果已保存至: {output_filepath}")

    except FileNotFoundError as e:
        print(f"错误: 找不到文件 {e.filename}。请确保 'standardInput.json' 和 'data.json' 文件存在于脚本所在目录。")
    except json.JSONDecodeError:
        print("错误: JSON文件格式无效，请检查文件内容。")
    except Exception as e:
        print(f"发生未知错误: {e}")