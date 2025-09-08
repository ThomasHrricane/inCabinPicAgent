import json

def normalize_gender(gender_str):
    """将不同的性别表述统一为'男', '女', 或 'unknown'"""
    if gender_str in ['女性', '女']:
        return '女'
    if gender_str in ['男性', '男']:
        return '男'
    return 'unknown'

def normalize_person_position(pos_from_cleaned_data):
    """将 cleaned_data3.json 中的位置映射到 parsed2_sorted.json 的位置"""
    mapping = {
        '副驾': '前排左',
        '主驾': '前排右',
        '二排左': '中排右',  # 注意：根据您的要求进行的特殊映射
        '二排右': '中排左',  # 注意：根据您的要求进行的特殊映射
        '三排左': '后排右',  # 注意：根据您的要求进行的特殊映射
        '三排右': '后排左',  # 注意：根据您的要求进行的特殊映射
        '过道': '过道' 
        # 其他未在映射中的位置将不会匹配成功
    }
    return mapping.get(pos_from_cleaned_data)

def normalize_object_position(pos_from_cleaned_data):
    """统一物品位置的表述"""
    # 复用人员位置的映射规则
    mapping = {
        '前排扶手箱': '中央扶手箱',
        '前排扶手箱-杯槽': '中央扶手箱-杯槽',
        '副驾': '前排左',
        '主驾': '前排右',
        '二排左': '中排右',
        '二排右': '中排左',
        '三排左': '后排右',
        '三排右': '后排左',
        '过道': '过道'
    }
    return mapping.get(pos_from_cleaned_data, pos_from_cleaned_data)


def detailed_comparison(file_cleaned, file_parsed):
    """
    对两个JSON文件进行详细的、基于规则的比较，并计算匹配率。
    """
    try:
        with open(file_cleaned, 'r', encoding='utf-8') as f:
            data_cleaned = json.load(f)
        with open(file_parsed, 'r', encoding='utf-8') as f:
            data_parsed = json.load(f)
    except FileNotFoundError as e:
        print(f"错误: 文件未找到 -> {e}")
        return

    # 初始化人员信息计数器
    person_total_count = 0
    person_matches = {
        '年龄': 0, '性别': 0, '位置': 0, '上衣样式': 0,
        '上衣颜色': 0, '下装样式': 0, '下装颜色': 0
    }

    # 初始化物品信息计数器
    object_total_count = 0
    object_matches = {'物品': 0, '位置': 0}

    # --- 第一部分：比对人员信息 ---
    for i in range(len(data_cleaned)):
        record_cleaned = data_cleaned[i]
        record_parsed = data_parsed[i]

        persons_cleaned = record_cleaned.get('persons', [])
        persons_parsed = record_parsed.get('人', {}).get('具体信息', [])

        person_total_count += len(persons_cleaned)

        # 按次序一一对应进行比较
        for p_cleaned, p_parsed in zip(persons_cleaned, persons_parsed):
            # 年龄
            if str(p_cleaned.get('年龄', '')).lower() == str(p_parsed.get('年龄', '')).lower():
                person_matches['年龄'] += 1
            
            # 性别
            if normalize_gender(p_cleaned.get('性别', '')) == normalize_gender(p_parsed.get('性别', '')):
                 person_matches['性别'] += 1

            # 位置
            if normalize_person_position(p_cleaned.get('位置', '')) == p_parsed.get('位置', ''):
                person_matches['位置'] += 1

            # 衣裤信息
            cleaned_clothes = p_cleaned.get('衣裤', {})
            
            # 上衣样式 (包含关系)
            style1_cleaned = cleaned_clothes.get('着装1类型', '')
            style_parsed = p_parsed.get('上衣样式', '')
            if style_parsed and style_parsed.lower() != 'unknown' and style_parsed in style1_cleaned:
                 person_matches['上衣样式'] += 1
            elif style_parsed.lower() == 'unknown' and style1_cleaned.lower() == 'unknown':
                 person_matches['上衣样式'] += 1

            # 上衣颜色
            color1_cleaned = cleaned_clothes.get('着装1颜色', '').lower()
            color_parsed = p_parsed.get('上衣颜色', '').lower()
            if color1_cleaned == color_parsed:
                person_matches['上衣颜色'] += 1

            # 下装样式
            style2_cleaned = cleaned_clothes.get('着装2类型', '').lower()
            style2_parsed = p_parsed.get('下装样式', '').lower()
            if style2_cleaned == style2_parsed:
                person_matches['下装样式'] += 1

            # 下装颜色
            color2_cleaned = cleaned_clothes.get('着装2颜色', '').lower()
            color2_parsed = p_parsed.get('下装颜色', '').lower()
            if color2_cleaned == color2_parsed:
                person_matches['下装颜色'] += 1

    # --- 第二部分：比对物品信息 (无序) ---
    for i in range(len(data_cleaned)):
        record_cleaned = data_cleaned[i]
        record_parsed = data_parsed[i]

        objects_cleaned = record_cleaned.get('objects', [])
        objects_parsed = record_parsed.get('物品', {}).get('具体信息', [])
        
        object_total_count += len(objects_cleaned)
        
        # 标记cleaned中的物品是否已被匹配，防止重复计数
        matched_indices = [False] * len(objects_cleaned)

        # 优先寻找“物品”和“位置”都匹配的项
        for o_parsed in objects_parsed:
            parsed_kind = o_parsed.get('种类', '').lower()
            parsed_pos = o_parsed.get('位置', '')
            
            # if parsed_kind == 'unknown': continue # unknown 物品不参与匹配

            for j, o_cleaned in enumerate(objects_cleaned):
                if not matched_indices[j]:
                    cleaned_kind = o_cleaned.get('物品', '').lower()
                    cleaned_pos_normalized = normalize_object_position(o_cleaned.get('位置', ''))
                    
                    if parsed_kind == cleaned_kind and parsed_pos == cleaned_pos_normalized:
                        object_matches['物品'] += 1
                        object_matches['位置'] += 1
                        matched_indices[j] = True
                        break # 已找到完全匹配，跳出内层循环

        # 再为剩下未匹配的 parsed 物品寻找仅“物品”匹配的项
        for o_parsed in objects_parsed:
            # 检查这个parsed item是否已在上一轮中匹配成功
            is_already_matched = False
            for j, o_cleaned in enumerate(objects_cleaned):
                 if matched_indices[j] and o_parsed.get('种类','').lower() == o_cleaned.get('物品','').lower() and o_parsed.get('位置','') == normalize_object_position(o_cleaned.get('位置','')):
                     is_already_matched = True
                     break
            if is_already_matched: continue
            
            parsed_kind = o_parsed.get('种类', '').lower()
            # if parsed_kind == 'unknown': continue

            for j, o_cleaned in enumerate(objects_cleaned):
                if not matched_indices[j]:
                    cleaned_kind = o_cleaned.get('物品', '').lower()
                    if parsed_kind == cleaned_kind:
                        object_matches['物品'] += 1
                        matched_indices[j] = True
                        break # 仅物品匹配，跳出内层循环
    
    # --- 第三部分：计算并打印结果 ---
    print("--- 人员信息匹配率 ---")
    if person_total_count > 0:
        for key, value in person_matches.items():
            rate = (value / person_total_count) * 100
            print(f"标签【{key}】的匹配率: {rate:.2f}% ({value}/{person_total_count})")
    else:
        print("在 cleaned_data3.json 中未找到人员信息。")

    print("\n--- 物品信息匹配率 ---")
    if object_total_count > 0:
        item_rate = (object_matches['物品'] / object_total_count) * 100
        pos_rate = (object_matches['位置'] / object_total_count) * 100
        print(f"标签【物品种类】的匹配率: {item_rate:.2f}% ({object_matches['物品']}/{object_total_count})")
        print(f"标签【物品位置】的匹配率: {pos_rate:.2f}% ({object_matches['位置']}/{object_total_count})")
    else:
        print("在 cleaned_data3.json 中未找到物品信息。")

# --- 主程序入口 ---
if __name__ == "__main__":
    file1 = './data/cleaned_data6.json'
    file2 = './data/parsed3_sorted.json'
    detailed_comparison(file1, file2)