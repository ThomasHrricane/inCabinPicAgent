import json
from collections import defaultdict, Counter
from copy import deepcopy

input_data = []

# ---------- Step 1: 读取并过滤 JSONL 数据 ----------
with open("./evaluated_output/part1_evaluated.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        try:
            # line = line.replace("：", ":")
            item = json.loads(line.strip())
            if "gemini_response" in item and "image_path" in item:
                input_data.append(item)
            else:
                print("⚠️ 跳过结构异常数据：", item)
        except Exception as e:
            print(f"❌ JSON 解析失败: {e}")

# ---------- Step 2: 按图片编号分组 ----------
grouped = defaultdict(list)
for item in input_data:
    image_path = item["image_path"]
    image_num = int(image_path.split("/")[-1].split(".")[0])  # 提取编号
    grouped[f"pic_{image_num}"].append(item["gemini_response"])


# ---------- 工具函数：可哈希化 ----------
def make_hashable(v):
    if isinstance(v, list):
        return tuple(v)
    return v

def make_unhashable(v):
    if isinstance(v, tuple):
        return list(v)
    return v


# ---------- Step 3: 合并多个响应 ----------
def compare_and_merge(responses):
    merged = deepcopy(responses[0])

    for key in merged:
        if isinstance(merged[key], dict):
            for subkey in merged[key]:
                if isinstance(merged[key][subkey], list):
                    for i in range(len(merged[key][subkey])):
                        for attr in merged[key][subkey][i]:
                            values = []
                            for r in responses:
                                try:
                                    val = r[key][subkey][i].get(attr, "missing")
                                except:
                                    val = "missing"
                                values.append(val)

                            hashable_values = [make_hashable(v) for v in values]
                            count = Counter(hashable_values)
                            most_common = count.most_common()

                            if len(most_common) == 1:
                                continue
                            elif most_common[0][1] > 1:
                                majority = most_common[0][0]
                                others = [make_unhashable(v) for v in set(hashable_values) if v != majority]
                                merged[key][subkey][i][attr] = make_unhashable(majority) if isinstance(majority, tuple) else majority
                                if others:
                                    merged[key][subkey][i][attr] = f"{merged[key][subkey][i][attr]}  // {', '.join(map(str, others))}"
                            else:
                                merged[key][subkey][i][attr] = f"{values[0]}  // {values[1]}, {values[2]}"
                else:
                    # 非列表：人数 / 物品数 / 宠物数等
                    values = [r[key][subkey] for r in responses]
                    hashable_values = [make_hashable(v) for v in values]
                    count = Counter(hashable_values)
                    most_common = count.most_common()

                    if len(most_common) == 1:
                        continue
                    elif most_common[0][1] > 1:
                        majority = most_common[0][0]
                        others = [make_unhashable(v) for v in set(hashable_values) if v != majority]
                        merged[key][subkey] = make_unhashable(majority) if isinstance(majority, tuple) else majority
                        if others:
                            merged[key][subkey] = f"{merged[key][subkey]}  // {', '.join(map(str, others))}"
                    else:
                        merged[key][subkey] = f"{values[0]}  // {values[1]}, {values[2]}"
        else:
            # 顶层字段：是否为黑夜、是否有中央扶手箱
            values = [r.get(key, "missing") for r in responses]
            hashable_values = [make_hashable(v) for v in values]
            count = Counter(hashable_values)
            most_common = count.most_common()

            if len(most_common) == 1:
                continue
            elif most_common[0][1] > 1:
                majority = most_common[0][0]
                others = [make_unhashable(v) for v in set(hashable_values) if v != majority]
                merged[key] = make_unhashable(majority) if isinstance(majority, tuple) else majority
                if others:
                    merged[key] = f"{merged[key]}  // {', '.join(map(str, others))}"
            else:
                merged[key] = f"{values[0]}  // {values[1]}, {values[2]}"

    return merged


# ---------- Step 4: 合并并保存 ----------
final_result = {}
for pic_key, responses in grouped.items():
    if len(responses) == 3:
        merged = compare_and_merge(responses)
        final_result[pic_key] = merged
    else:
        print(f"⚠️ 跳过 {pic_key}：响应数量不足3条，仅使用第1条")
        final_result[pic_key] = responses[0]

# ---------- Step 5: 保存结果 ----------
with open("gi_action.json", "w", encoding="utf-8") as f:
    json.dump(final_result, f, ensure_ascii=False, indent=2)

print("✅ 合并完成，结果保存在 gi_action.json")
