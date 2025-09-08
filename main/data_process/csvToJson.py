import csv
import json

def compare_and_get(row, key_suffix):
    """
    比较并获取两位标注员的标注内容。
    - key_suffix: 列名的共同后缀，例如 "person1-年龄"
    """
    key1 = f'标注员1-{key_suffix}'
    key2 = f'标注员2-{key_suffix}'
    
    # 获取两个标注员的值，如果列不存在则视为空字符串
    val1 = row.get(key1, '').strip()
    val2 = row.get(key2, '').strip()

    if val1 == val2:
        return val1
    else:
        # 如果其中一方为空，也明确标注出来
        if not val1: val1 = "EMPTY"
        if not val2: val2 = "EMPTY"
        return f"标注员1: {val1} ## 标注员2: {val2}"

def process_csv_to_json(input_file='data.csv', output_file='comparison_output.json'):
    """
    主函数，读取CSV，处理数据，并写入JSON文件。
    """
    results = []
    
    # 使用 utf-8-sig 编码以处理可能存在的 BOM (Byte Order Mark)
    with open(input_file, mode='r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            # 基础信息，直接从CSV行中获取
            record = {
                "id": row.get('id', ''),
                "url": row.get('url', ''),
                "工单ID": row.get('工单ID(多盲工单)', ''),
                "一致性": row.get('一致性', '')
            }
            
            # 对比通用信息
            record['general_info'] = {
                "车内人数": compare_and_get(row, '车内人数'),
                "车内物品数": compare_and_get(row, '车内物品数'),
                "车内宠物数": compare_and_get(row, '车内宠物数'),
                "晚上": compare_and_get(row, '晚上')
            }
            
            # 处理人员信息 (假设最多有6个人)
            persons = []
            for i in range(1, 7): 
                if row.get(f'标注员1-person{i}-年龄') or row.get(f'标注员2-person{i}-年龄'):
                    person = {
                        "person_id": i,
                        "年龄": compare_and_get(row, f'person{i}-年龄'),
                        "性别": compare_and_get(row, f'person{i}-性别'),
                        "位置": compare_and_get(row, f'person{i}-位置'),
                        "行为": compare_and_get(row, f'person{i}-行为'),
                        "衣裤": {
                            "着装1类型": compare_and_get(row, f'person{i}-衣裤-着装1类型'),
                            "着装1颜色": compare_and_get(row, f'person{i}-衣裤-着装1颜色'),
                            "着装2类型": compare_and_get(row, f'person{i}-衣裤-着装2类型'),
                            "着装2颜色": compare_and_get(row, f'person{i}-衣裤-着装2颜色')
                        }
                    }
                    persons.append(person)
            record['persons'] = persons

            # ---【代码修正处】---
            # 修正了物品列名的格式，现在可以正确提取物品信息
            objects = []
            for i in range(1, 8): # 假设最多有20个物品
                # 物品名称的列名后缀很可能是 "物品1", "物品2" ...
                item_name_suffix = f'good{i}-种类'
                # 物品位置的列名后缀很可能是 "物品1-位置", "物品2-位置" ...
                item_location_suffix = f'good{i}-位置'

                # 检查两位标注员是否至少有一位填写了物品名称
                if row.get(f'标注员1-{item_name_suffix}') or row.get(f'标注员2-{item_name_suffix}'):
                    item = {
                        "object_id": i,
                        "物品": compare_and_get(row, item_name_suffix),
                        "位置": compare_and_get(row, item_location_suffix)
                    }
                    objects.append(item)
            record['objects'] = objects
        

            pets = []
            for i in range(1, 3): # 
                # 物品名称的列名后缀很可能是 "物品1", "物品2" ...
                item_name_suffix = f'pet{i}-种类'
                # 物品位置的列名后缀很可能是 "物品1-位置", "物品2-位置" ...
                item_location_suffix = f'pet{i}-位置'

                # 检查两位标注员是否至少有一位填写了物品名称
                if row.get(f'标注员1-{item_name_suffix}') or row.get(f'标注员2-{item_name_suffix}'):
                    item = {
                        "pet_id": i,
                        "物品": compare_and_get(row, item_name_suffix),
                        "位置": compare_and_get(row, item_location_suffix)
                    }
                    pets.append(item)
            record['pets'] = pets
            
            results.append(record)

    # 将处理后的结果写入JSON文件
    with open(output_file, 'w', encoding='utf-8') as jsonfile:
        json.dump(results, jsonfile, ensure_ascii=False, indent=4)
        
    print(f"处理完成！结果已保存到 {output_file}")

# --- 执行脚本 ---
# 确保您的CSV文件名为 'data.csv'，或者修改下面的文件名
process_csv_to_json('./data/data6.csv', './data/comparison_output6.json')