import json

# 输入输出文件路径
input_file = "./outputs/parsed_responses.json"          # 原始文件
output_file = "./outputs/parsed_responses_processed.json"  # 处理后文件


# 读取原始 JSON 文件
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

processed = []
for idx, item in enumerate(data, start=1):
    # 给每个项加上 id
    item_with_id = {"id": idx, **item}

    # 遍历 “人” -> “具体信息”，过滤行为列表
    people = item_with_id.get("人", {})
    for person in people.get("具体信息", []):
        actions = person.get("行为", [])
        # 只保留值为 "是" 的项
        filtered_actions = [a for a in actions if list(a.values())[0] == "是"]
        person["行为"] = filtered_actions

    processed.append(item_with_id)

# 保存处理后的结果
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(processed, f, ensure_ascii=False, indent=2)

print(f"处理完成，结果已保存到 {output_file}")
