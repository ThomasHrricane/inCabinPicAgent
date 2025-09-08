import json

# 读取之前保存的转义后的字符串
with open("outputs/standard_string.txt", "r", encoding="utf-8") as f:
    escaped_string = f.read()

# 反转处理：把转义字符串转回原始带换行格式的文本
original_text = json.loads(escaped_string)

# 输出为 markdown 显示效果
print("### 📄 原始文本 (Markdown显示)\n")
print("```")
print(original_text)
print("```")

# 如果需要再写回文件（带换行的正常文本）
with open("outputs/original_text.txt", "w", encoding="utf-8") as f:
    f.write(original_text)

print("✅ 已恢复为原始可读文本")
