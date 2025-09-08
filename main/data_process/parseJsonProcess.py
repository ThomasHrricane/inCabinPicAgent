import json
with open("outputs/parsed_responses.json", "r", encoding="utf-8") as f:
    data = json.load(f)
# 给每个字典加上顺序 id
for idx, item in enumerate(data, start=1):
    item["id"] = idx

# 转换为 JSON 字符串，确保中文不转义
result = json.dumps(data, ensure_ascii=False, indent=4)

print(result)

# 如果需要保存到文件
with open("outputs/data_with_id.json", "w", encoding="utf-8") as f:
    f.write(result)