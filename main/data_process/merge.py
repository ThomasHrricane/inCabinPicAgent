# import json
# from collections import defaultdict
# from copy import deepcopy

# # 假设已经从你贴的文本加载到列表中
# input_data = [
#     # 把你提供的6条数据粘贴为字典项放在这个列表中……
#     # 示例结构：
#     # {"image_path": "...1.jpg", "gemini_response": {...}},
# ]

# with open("gi.jsonl", "r", encoding="utf-8") as f:
#     for line in f.readlines():
#         item = json.loads(line.strip())
#         input_data.append(item)


# # 按图片编号聚合结果
# grouped = defaultdict(list)
# for item in input_data:
#     image_path = item["image_path"]
#     image_num = int(image_path.split("/")[-1].split(".")[0])  # 提取数字编号
#     grouped[f"pic_{image_num}"].append(item["gemini_response"])

# # 比较字段差异的辅助函数
# def compare_and_merge(responses):
#     merged = deepcopy(responses[0])
#     for key in merged:
#         if isinstance(merged[key], dict):
#             for subkey in merged[key]:
#                 if isinstance(merged[key][subkey], list):
#                     for i, person in enumerate(merged[key][subkey]):
#                         if i >= len(responses[1][key][subkey]) or i >= len(responses[2][key][subkey]):
#                             continue
#                         for attr in person:
#                             values = {
#                                 responses[0][key][subkey][i].get(attr, "missing"),
#                                 responses[1][key][subkey][i].get(attr, "missing"),
#                                 responses[2][key][subkey][i].get(attr, "missing")
#                             }
#                             if len(values) > 1:
#                                 merged[key][subkey][i][attr] += f"  // " + ", ".join(values - {merged[key][subkey][i][attr]})
#                 else:
#                     values = {
#                         responses[0][key][subkey],
#                         responses[1][key][subkey],
#                         responses[2][key][subkey]
#                     }
#                     if len(values) > 1:
#                         merged[key][subkey] += f"  // " + ", ".join(values - {merged[key][subkey]})
#         else:
#             values = {resp[key] for resp in responses}
#             if len(values) > 1:
#                 merged[key] += f"  // " + ", ".join(values - {merged[key]})
#     return merged

# # 生成最终结构
# final_result = {}
# for pic_key, responses in grouped.items():
#     if len(responses) == 3:
#         merged = compare_and_merge(responses)
#         final_result[pic_key] = merged
#     else:
#         final_result[pic_key] = responses[0]  # fallback: 不足三次就取第一个

# # 写入文件
# with open("gemini_merged_results.json", "w", encoding="utf-8") as f:
#     json.dump(final_result, f, ensure_ascii=False, indent=2)

# print("合并完成，文件已保存为 gemini_merged_results.json")



# import json
# from collections import defaultdict, Counter
# from copy import deepcopy

# input_data = []

# # 读取 JSONL 文件
# with open("./evaluated_output/go.jsonl", "r", encoding="utf-8") as f:
#     for line in f.readlines():
#         item = json.loads(line.strip())
#         input_data.append(item)

# # 按图片编号聚合结果
# grouped = defaultdict(list)
# for item in input_data:
#     image_path = item["image_path"]
#     image_num = int(image_path.split("/")[-1].split(".")[0])  # 提取数字编号
#     grouped[f"pic_{image_num}"].append(item["gemini_response"])


# # 多数优先合并
# def compare_and_merge(responses):
#     merged = deepcopy(responses[0])

#     for key in merged:
#         if isinstance(merged[key], dict):
#             for subkey in merged[key]:
#                 if isinstance(merged[key][subkey], list):
#                     for i, person in enumerate(merged[key][subkey]):
#                         # 检查该 index 是否在其他响应中存在
#                         if (
#                             i >= len(responses[1][key][subkey])
#                             or i >= len(responses[2][key][subkey])
#                         ):
#                             continue
#                         for attr in person:
#                             v0 = responses[0][key][subkey][i].get(attr, "missing")
#                             v1 = responses[1][key][subkey][i].get(attr, "missing")
#                             v2 = responses[2][key][subkey][i].get(attr, "missing")
#                             values = [v0, v1, v2]
#                             count = Counter(values)
#                             most_common = count.most_common()

#                             if len(most_common) == 1:
#                                 continue  # 三次一致，无需处理
#                             elif most_common[0][1] > 1:
#                                 majority = most_common[0][0]
#                                 others = [v for v in set(values) if v != majority]
#                                 merged[key][subkey][i][attr] = (
#                                     majority + f"  // " + ", ".join(others)
#                                 )
#                             else:
#                                 # 三次都不同，保留原顺序
#                                 merged[key][subkey][i][attr] = (
#                                     v0 + f"  // {v1}, {v2}"
#                                 )
#                 else:
#                     v0 = responses[0][key][subkey]
#                     v1 = responses[1][key][subkey]
#                     v2 = responses[2][key][subkey]
#                     values = [v0, v1, v2]
#                     count = Counter(values)
#                     most_common = count.most_common()
#                     if len(most_common) == 1:
#                         continue
#                     elif most_common[0][1] > 1:
#                         majority = most_common[0][0]
#                         others = [v for v in set(values) if v != majority]
#                         merged[key][subkey] = majority + f"  // " + ", ".join(others)
#                     else:
#                         merged[key][subkey] = v0 + f"  // {v1}, {v2}"
#         else:
#             v0 = responses[0][key]
#             v1 = responses[1][key]
#             v2 = responses[2][key]
#             values = [v0, v1, v2]
#             count = Counter(values)
#             most_common = count.most_common()
#             if len(most_common) == 1:
#                 continue
#             elif most_common[0][1] > 1:
#                 majority = most_common[0][0]
#                 others = [v for v in set(values) if v != majority]
#                 merged[key] = majority + f"  // " + ", ".join(others)
#             else:
#                 merged[key] = v0 + f"  // {v1}, {v2}"
#     return merged


# # 合并生成结果
# final_result = {}
# for pic_key, responses in grouped.items():
#     if len(responses) == 3:
#         merged = compare_and_merge(responses)
#         final_result[pic_key] = merged
#     else:
#         final_result[pic_key] = responses[0]

# # 输出为 json 文件
# with open("go_merged_results.json", "w", encoding="utf-8") as f:
#     json.dump(final_result, f, ensure_ascii=False, indent=2)

# print("✅ 合并完成，文件已保存为 gemini_merged_results.json")





import json
from collections import defaultdict, Counter
from copy import deepcopy

input_data = []

# 读取 JSONL 文件
with open("./evaluated_output/part1_evaluated.jsonl", "r", encoding="utf-8") as f:
    for line in f.readlines():
        item = json.loads(line.strip())
        input_data.append(item)

# 按图片编号聚合结果
grouped = defaultdict(list)
for item in input_data:
    image_path = item["image_path"]
    image_num = int(image_path.split("/")[-1].split(".")[0])  # 提取数字编号
    grouped[f"pic_{image_num}"].append(item["gemini_response"])


# 多数优先合并
def compare_and_merge(responses):
    merged = deepcopy(responses[0])

    for key in merged:
        if isinstance(merged[key], dict):
            for subkey in merged[key]:
                if isinstance(merged[key][subkey], list):
                    for i, person in enumerate(merged[key][subkey]):
                        # 检查该 index 是否在其他响应中存在
                        if (
                            i >= len(responses[1][key][subkey])
                            or i >= len(responses[2][key][subkey])
                        ):
                            continue
                        for attr in person:
                            v0 = responses[0][key][subkey][i].get(attr, "missing")
                            v1 = responses[1][key][subkey][i].get(attr, "missing")
                            v2 = responses[2][key][subkey][i].get(attr, "missing")
                            values = [v0, v1, v2]
                            count = Counter(values)
                            most_common = count.most_common()

                            if len(most_common) == 1:
                                continue  # 三次一致，无需处理
                            elif most_common[0][1] > 1:
                                majority = most_common[0][0]
                                others = [v for v in set(values) if v != majority]
                                merged[key][subkey][i][attr] = (
                                    majority + f"  // " + ", ".join(others)
                                )
                            else:
                                # 三次都不同，保留原顺序
                                merged[key][subkey][i][attr] = (
                                    v0 + f"  // {v1}, {v2}"
                                )
                else:
                    v0 = responses[0][key][subkey]
                    v1 = responses[1][key][subkey]
                    v2 = responses[2][key][subkey]
                    values = [v0, v1, v2]
                    count = Counter(values)
                    most_common = count.most_common()
                    if len(most_common) == 1:
                        continue
                    elif most_common[0][1] > 1:
                        majority = most_common[0][0]
                        others = [v for v in set(values) if v != majority]
                        merged[key][subkey] = majority + f"  // " + ", ".join(others)
                    else:
                        merged[key][subkey] = v0 + f"  // {v1}, {v2}"
        else:
            v0 = responses[0][key]
            v1 = responses[1][key]
            v2 = responses[2][key]
            values = [v0, v1, v2]
            count = Counter(values)
            most_common = count.most_common()
            if len(most_common) == 1:
                continue
            elif most_common[0][1] > 1:
                majority = most_common[0][0]
                others = [v for v in set(values) if v != majority]
                merged[key] = majority + f"  // " + ", ".join(others)
            else:
                merged[key] = v0 + f"  // {v1}, {v2}"
    return merged


# 合并生成结果
final_result = {}
for pic_key, responses in grouped.items():
    if len(responses) == 3:
        merged = compare_and_merge(responses)
        final_result[pic_key] = merged
    else:
        final_result[pic_key] = responses[0]

# 输出为 json 文件
with open("fuza_action.json", "w", encoding="utf-8") as f:
    json.dump(final_result, f, ensure_ascii=False, indent=2)

print("✅ 合并完成，文件已保存为 gemini_merged_results.json")
