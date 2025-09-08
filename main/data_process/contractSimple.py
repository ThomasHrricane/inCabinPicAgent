import json

def compare_json_files(file1_path, file2_path):
    """
    读取并比较两个JSON文件中的特定字段，并报告匹配项的数量。

    Args:
        file1_path (str): 第一个JSON文件的路径 (cleaned_data3.json)
        file2_path (str): 第二个JSON文件的路径 (parsed2.json)
    """
    try:
        with open(file1_path, 'r', encoding='utf-8') as f1:
            data1 = json.load(f1)
        with open(file2_path, 'r', encoding='utf-8') as f2:
            data2 = json.load(f2)
    except FileNotFoundError as e:
        print(f"错误: {e}。请确保文件路径正确。")
        return
    except json.JSONDecodeError as e:
        print(f"文件JSON格式错误: {e}")
        return

    # 初始化匹配计数器
    person_count_matches = 0
    item_count_matches = 0
    pet_count_matches = 0
    night_time_matches = 0

    # 获取记录数量（以较少的文件为准，防止索引越界）
    num_records = min(len(data1), len(data2))
    if num_records != 30:
        print(f"注意: 文件包含的记录数为 {num_records}，而非预期的30。")


    # 遍历并比较记录
    for i in range(num_records):
        record1 = data1[i]
        record2 = data2[i]

        # 1. 对比 "车内人数" 和 "人数"
        person_count1 = record1.get('general_info', {}).get('车内人数')
        person_count2 = record2.get('人', {}).get('人数')
        if str(person_count1) == str(person_count2):
            person_count_matches += 1

        # 2. 对比 "车内物品数" 和 "物品数"
        item_count1 = record1.get('general_info', {}).get('车内物品数')
        item_count2 = record2.get('物品', {}).get('物品数')
        if str(item_count1) == str(item_count2):
            item_count_matches += 1

        # 3. 对比 "车内宠物数" (假设文件2中没有宠物则为0)
        pet_count1 = record1.get('general_info', {}).get('车内宠物数', '0')
        # parsed2.json中没有宠物字段，我们假定其值为'0'
        pet_count2 = '0' 
        if str(pet_count1) == str(pet_count2):
            pet_count_matches += 1

        # 4. 对比 "晚上" 和 "是否为黑夜"
        is_night1 = record1.get('general_info', {}).get('晚上')
        is_night2 = record2.get('是否为黑夜')
        # 将不同的表达方式（如"是"/"否"）统一后比较
        normalized_night1 = '是' if is_night1 in ['是', True, 'true', 'Yes', '1'] else '否'
        normalized_night2 = '是' if is_night2 in ['是', True, 'true', 'Yes', '1'] else '否'
        if normalized_night1 == normalized_night2:
            night_time_matches += 1

    # 打印最终的匹配结果
    print("--- JSON文件对比结果 ---")
    print(f"总计对比了 {num_records} 项。")
    print(f"【车内人数】与【人数】匹配的数量: {person_count_matches}/{num_records}")
    print(f"【车内物品数】与【物品数】匹配的数量: {item_count_matches}/{num_records}")
    print(f"【车内宠物数】匹配的数量: {pet_count_matches}/{num_records}")
    print(f"【晚上】与【是否为黑夜】匹配的数量: {night_time_matches}/{num_records}")

# --- 主程序入口 ---
if __name__ == "__main__":
    # 定义你的JSON文件路径
    file1 = './data/cleaned_data6.json'
    file2 = './data/parsed3.json'
    
    # 执行对比函数
    compare_json_files(file1, file2)