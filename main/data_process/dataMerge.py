import json
import re

# 读取原始文件
with open("./outputs/results_a11.json", "r", encoding="utf-8") as f:
    data = json.load(f)

results = []

for item in data:
    response_text = item.get("response", "")
    
    # 去掉 ```json 和 ``` 包裹
    clean_text = re.sub(r"^```json\s*|\s*```$", "", response_text.strip(), flags=re.DOTALL)
    
    try:
        # 解析成真正的 JSON 对象
        response_json = json.loads(clean_text)
        results.append(response_json)
    except json.JSONDecodeError as e:
        print(f"⚠️ index {item.get('index')} 的 response 解析失败: {e}")
        continue

# 保存拼装后的标准 JSON 列表
with open("outputs/parsed_responses.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("✅ 已完成处理，所有 response 已拼装成标准 JSON 列表 outputs/parsed_responses11.json")
