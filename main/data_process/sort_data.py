import json
import re

def sort_parsed_data(input_file, output_file):
    """
    读取 parsed2.json 文件，对其中的人和物品信息进行排序，
    然后将结果写入一个新的JSON文件。

    Args:
        input_file (str): 输入的JSON文件路径 ('parsed2.json')。
        output_file (str): 输出排序后结果的JSON文件路径。
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误: 输入文件 '{input_file}' 未找到。请确保文件在正确的路径下。")
        return
    except json.JSONDecodeError:
        print(f"错误: 文件 '{input_file}' 的JSON格式无效。")
        return

    # --- 排序逻辑定义 ---

    # 1. 定义“人”的位置排序顺序
    person_position_order = {
        '前排右': 0, '前排左': 1, '中排右': 2, '中排左': 3, 
        '后排右': 4, '后排左': 5
    }

    def get_person_sort_key(person):
        """为“人”的排序提供键"""
        position = person.get('位置', '')
        # 规范化位置，去除括号内容，例如 "中排左（若有）" -> "中排左"
        normalized_position = re.sub(r'（若有）', '', position)
        # 对于未在排序规则中定义的位置，给予一个较大的默认值，使其排在后面
        return person_position_order.get(normalized_position, 99)

    # 2. 定义“物品”的排序逻辑
    def get_item_sort_key(item):
        """为“物品”的排序提供多级优先级的键"""
        kind = item.get('种类', 'unknown')
        location = item.get('位置', '')

        is_unknown = (kind == 'unknown')

        # 返回一个元组，Python会依次比较元组中的每个元素来实现多级排序
        if not is_unknown and location == '中央扶手箱':
            return (0, kind, location)  # 最高优先级
        elif not is_unknown and location == '中央扶手箱-杯槽':
            return (1, kind, location)  # 第二优先级
        elif not is_unknown:
            return (2, kind, location)  # 第三优先级
        else:
            return (3, kind, location)  # 最低优先级

    # --- 开始处理数据 ---
    for entry in data:
        # 排序人的“具体信息”
        if '人' in entry and '具体信息' in entry['人']:
            # 使用 lambda 函数和我们定义的key函数进行排序
            entry['人']['具体信息'].sort(key=get_person_sort_key)
        
        # 排序物品的“具体信息”
        if '物品' in entry and '具体信息' in entry['物品']:
            entry['物品']['具体信息'].sort(key=get_item_sort_key)

    # --- 保存结果到新文件 ---
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # json.dump 用于将Python对象写入JSON文件
            # ensure_ascii=False 保证中文字符正常显示
            # indent=4         使输出的JSON文件格式优美，易于阅读
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"处理完成！排序后的数据已保存到 '{output_file}'。")
    except IOError as e:
        print(f"错误: 无法写入文件 '{output_file}'。错误信息: {e}")


# --- 主程序入口 ---
if __name__ == "__main__":
    input_filename = './data/parsed3.json'
    output_filename = './data/parsed3_sorted.json'
    sort_parsed_data(input_filename, output_filename)