import json


with open("data/comparison_output6.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for idx, item in enumerate(data, start=1):
    # 删除指定字段（如果存在）
    item.pop("url", None)
    item.pop("工单ID", None)
    item.pop("一致性", None)
    # 修改 id 为顺序
    item["id"] = str(idx)

# 转换为 JSON 字符串，保证中文不转义
result = json.dumps(data, ensure_ascii=False, indent=4)

# 输出结果
print(result)

# 如果需要保存到文件
with open("data/cleaned_data6.json", "w", encoding="utf-8") as f:

    f.write(result)