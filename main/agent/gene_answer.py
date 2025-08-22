#!/usr/bin/env python3
"""
图文问答评估器
使用 Gemini API 根据文字说明和图片生成回答并分析质量。
"""
import os
import json
import base64
import argparse
import logging
from pathlib import Path
from typing import List, Dict
import time
import asyncio
import aiohttp
import pandas as pd
from PIL import Image
import io


# --- 设置日志 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Prompt 模板 ---
EVALUATION_PROMPT_TEMPLATE = """
{source_text}
角色: 你是一位车内识别助手。
任务: 严格按照json 格式,给出答案结果,答案均只能从备选项中选取并只选取一个,不要给出备选项中未出现的答案。以下为带有所有备选项的模版:
{{
    "人": {{
        "人数": "0,1,2,3,4,5,6",
        "具体信息": [
            {{
                "性别": "男,女,unknown",
                "位置": "前排左,前排右,中排左（若有）,中排右（若有）,后排左,后排右,过道,unknown",
                "配饰": "眼镜,围巾,帽子,耳机,手表,墨镜,口罩,耳坠（非耳钉）,靴子,unknown",
                "行为": [
                    {{"是否在阅读":"是,否"}},
                    {{"是否在化妆":"是,否"}},
                    {{"是否在吃东西":"是,否"}},
                    {{"是否在托腮思考":"是,否"}},
                    {{"是否在玩手机":"是,否"}},
                    {{"是否在打电话":"是,否"}},
                    {{"是否在吸烟":"是,否"}},
                    {{"是否在点烟":"是,否"}},
                    {{"是否在睡觉":"是,否"}},
                    {{"是否在抱猫":"是,否"}},
                    {{"是否在抱狗":"是,否"}},
                    {{"是否头或手伸出窗外":"是,否"}},
                    {{"是否在哭闹":"是,否"}},
                    {{"是否未系安全带":"是,否"}},
                    {{"是否食指指向前":"是,否"}},
                    {{"是否食指指向上":"是,否"}},
                    {{"是否食指指向下":"是,否"}},
                    {{"是否食指指向左":"是,否"}},
                    {{"是否食指指向右":"是,否"}},
                    {{"是否手触碰车顶屏幕":"是,否"}},
                    {{"是否在站立":"是,否"}}
                ]
            }}
        ]
    }}
}}



背景:
- 目标: 根据给出的图片,将json 模版中各选择题选择出最合适的答案
输出要求:
- 一个个分析每个选项，对于行为中的每一项问题一步步来分析，尤其需要重视行为列表中的每一个选择，确保识别图片与思考完整后再给出每一个行为列表选择的答案
- 选择的答案必须为该问题备选项中的项,如果不是则重新从备选项中选择
- 以图片左侧为左,右侧为右。
- 如有多个人,按照前排左、前排右、中排左（若有）、中排右（若有）、后排左、后排右 顺序展开
- 若有两排座位,用前排、后排代称。若有三排座位,用前排、中排、后排代称,即此时第二排只能用中排代称。
- 只输出json ,不要给出解释或说明
- 人的具体信息列表这里要根据其人数来确定列表中应有几项字典并自动增加。
- 结合常识判断各行为标签的共存是否可能,如一般情况下不会有人在阅读的同时在化妆,因此如果有此情况则将其改为否
- 年龄14岁以下认为是儿童,能在车内站立也认为是儿童
- 两排座位之间为过道,三排座位车非前排时,同一排两座位间也为过道

格式: 输出为json
- 避免:
  1. 不要输出任何其他内容,只输出该json模版答案替换后的版本
  2. 不要给出未知,可能是,不明,不知晓等所有表示不确定的词语,都用unknown代替
  3. 衣服的样式答案不要给出多种可能,给出备选项中最可能的一种,完全无法确定就给unknown
  4. 颜色的选择不要给出深绿、蓝绿这些,严格从备选项中进行选择
- 示例 (输出参考):
- 好的输出:
{{
"人": {{
"人数": "2",
"具体信息": [
{{
"性别": "男",
"位置": "前排右",
"配饰":"眼镜,围巾",
"行为":[
{{"是否在阅读":"是,否"}},
{{"是否在化妆":"否"}},
{{"是否在吃东西":"否"}},
{{"是否在托腮思考":"否"}},
{{"是否在玩手机":"否"}},
{{"是否在打电话":"否"}},
{{"是否在吸烟":"否"}},
{{"是否在点烟":"否"}},
{{"是否在睡觉":"否"}},
{{"是否在抱猫":"否"}},
{{"是否在抱狗":"否"}},
{{"是否头或手伸出窗外":"否"}},
{{"是否在哭闹":"否"}},
{{"是否未系安全带":"是"}},
{{"是否食指指向前":"否"}},
{{"是否食指指向上":"否"}},
{{"是否食指指向下":"否"}},
{{"是否食指指向左":"否"}},
{{"是否食指指向右":"否"}},
{{"是否手触碰车顶屏幕":"否"}},
{{"是否在站立":"否"}}
]
}},
{{
"性别": "女",
"位置": "后排右",
"配饰":"手表,墨镜,口罩,围巾",
"行为":[
{{"是否在阅读":"是"}},
{{"是否在化妆":"否"}},
{{"是否在吃东西":"否"}},
{{"是否在托腮思考":"否"}},
{{"是否在玩手机":"否"}},
{{"是否在打电话":"否"}},
{{"是否在吸烟":"否"}},
{{"是否在点烟":"否"}},
{{"是否在睡觉":"否"}},
{{"是否在抱猫":"否"}},
{{"是否在抱狗":"否"}},
{{"是否头或手伸出窗外":"否"}},
{{"是否在哭闹":"否"}},
{{"是否未系安全带":"是"}},
{{"是否食指指向前":"否"}},
{{"是否食指指向上":"否"}},
{{"是否食指指向下":"否"}},
{{"是否食指指向左":"否"}},
{{"是否食指指向右":"否"}},
{{"是否手触碰车顶屏幕":"否"}},
{{"是否在站立":"否"}}
]
}}
]
}}
}}

- 避免的输出:
{{
"人": {{
"人数": "一",
"具体信息": [{{"性别":"未知","位置":"车上","配饰":"太阳镜,高跟靴子",
"行为":[
{{"是否在阅读":"是"}},
{{"是否在化妆":"是"}},
{{"是否在吃东西":"不清楚"}},
{{"是否在托腮思考":"是"}},
{{"是否在玩手机":"否"}},
{{"是否在打电话":"否"}},
{{"是否在吸烟":"是"}},
{{"是否在点烟":"是"}},
{{"是否在睡觉":"否"}},
{{"是否在抱猫":"否"}},
{{"是否在抱狗":"是"}},
{{"是否头或手伸出窗外":"不确定"}},
{{"是否在哭闹":"是"}},
{{"是否未系安全带":"否"}},
{{"是否食指指向前":"否"}},
{{"是否食指指向上":"否"}},
{{"是否食指指向下":"是"}},
{{"是否食指指向左":"是"}},
{{"是否食指指向右":"否"}},
{{"是否手触碰车顶屏幕":"否"}},
{{"是否在站立":"是"}}
]
}}]
}}
}}

"""

class GeminiEvaluator:
    """图文评估处理器"""
    def __init__(self, api_key: str, base_url: str = None, model: str = "gemini-2.5-flash-preview-05-20-nothinking"): # type: ignore
        self.api_key = api_key
        self.base_url = base_url or "https://one-api.modelbest.co/v1"
        self.model = model
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    
    def encode_image(self, image_path: str, max_size: tuple = (2400, 1600)) -> str:
        """更接近 GPT-4o 网页端的图像编码器:压缩图像并转为 Base64"""
        try:
            with Image.open(image_path) as img:
                img = img.convert("RGB")  # 确保无 alpha 通道

                # 如果图像大于设定尺寸则缩放
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)

                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=85)  # 控制质量以减少体积
                buffer.seek(0)

                encoded = base64.b64encode(buffer.read()).decode("utf-8")

                logger.debug(f"图像编码完成,base64 长度:{len(encoded)} 字符")
                return encoded

        except Exception as e:
            logger.error(f"图片处理失败: {e}")
            raise

    
    async def evaluate_pair(self, source_text: str, image_path: str):
        """评估图文输入对,增强为类似 ChatGPT 网页版风格"""
        if not source_text or not image_path or not os.path.exists(image_path):
            return {"error": "Source text 或图片路径为空/无效"}

        image_base64 = self.encode_image(image_path)

        # ✅ 新增:更接近 ChatGPT 的 system prompt
        system_prompt = (
 "You are a multimodal assistant that can precisely understand and interpret images along with instructions."
    " When asked to provide answers in a structured JSON format, follow the format strictly."
    " Do not include any extra explanation or commentary."
    " Respond only with a valid JSON object when asked to output in that format."
        )

        user_prompt = EVALUATION_PROMPT_TEMPLATE.format(source_text=source_text)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "temperature": 0.3,
            "top_p": 1.0,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]}
            ]
        }

        try:
            async with self.session.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=300) as response: # type: ignore
                if response.status == 200:
                    result = await response.json()
                    content = result['choices'][0]['message']['content']
                    print(image_path)
                    print(f"模型输出: {content}")

                    # ✅ 更健壮的 JSON 清洗逻辑
                    if content.strip().startswith("```json"):
                        content = content.strip()[7:]
                        content = content.strip("`").strip()

                    try:
                        evaluation_data = json.loads(content)
                        logger.info("图文任务成功。")
                        return evaluation_data
                    except json.JSONDecodeError:
                        logger.warning("输出非标准 JSON,原始输出已返回。")
                        return {"error": "无法解析模型输出", "raw_response": content}
                else:
                    error_text = await response.text()
                    return {"error": f"API Error {response.status}", "details": error_text}
        except asyncio.TimeoutError:
            return {"error": "请求超时", "details": "Request timeout"}
        except aiohttp.ClientError as e:
            return {"error": "网络连接失败", "details": str(e)}




    # async def evaluate_pair(self, source_text: str, image_path: str):
    #     """评估图文输入对"""
    #     if not source_text or not image_path or not os.path.exists(image_path):
    #         return {"error": "Source text 或图片路径为空/无效"}

    #     image_base64 = self.encode_image(image_path)
    #     prompt = EVALUATION_PROMPT_TEMPLATE.format(source_text=source_text)

    #     try:
    #         headers = {
    #             "Authorization": f"Bearer {self.api_key}",
    #             "Content-Type": "application/json"
    #         }

    #         payload = {
    #             "model": self.model,
    #             "messages": [
    #                 {"role": "user", "content": [
    #                     {"type": "text", "text": prompt},
    #                     {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
    #                 ]}
    #             ],
    #             "temperature": 0.3,
    #             "top_p": 1.0,
    #             "frequency_penalty": 0,
    #             "presence_penalty": 0

    #         }
    #         try:
    #             async with self.session.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=300) as response: # type: ignore
    #                 if response.status == 200:
    #                     text_content = await response.text()
    #                     print(text_content)
                        
    #                     json_content = json.loads(text_content)
    #                     content = json_content['choices'][0]['message']['content']
    #                     if content.startswith("```json"):
    #                         content = content[7:]
    #                         content = content.strip("```")
                        
    #                     print(type(content))
    #                     print("#########################")
    #                     print(content)
    #                     print("#########################")
    #                     try:
    #                         evaluation_data = json.loads(content)
    #                         logger.info(f"图文任务成功,置信度评分: {evaluation_data.get('confidence')}/10")
    #                         return evaluation_data
    #                     except json.JSONDecodeError:
    #                         logger.error(f"无法解析JSON: {content}")
    #                         return {"error": "无法解析模型输出", "raw_response": content}
    #                 else:
    #                     error_text = await response.text()
    #                     logger.error(f"API请求失败: {response.status} - {error_text}")
    #                     return {"error": f"API Error {response.status}", "details": error_text}
    #         except asyncio.TimeoutError:
    #             return {"error": "请求超时", "details": "Request timeout"}
    #         except aiohttp.ClientError as e:
    #             return {"error": "网络连接失败", "details": str(e)}
    #     except Exception as e:
    #         logger.error(f"图文评估失败: {e}")
    #         return {"error": "异常", "details": str(e)}




def get_jsonl_files(folder_path: str) -> List[Path]:
    folder = Path(folder_path)
    if not folder.is_dir():
        raise FileNotFoundError(f"文件夹不存在: {folder_path}")
    files = sorted(list(folder.rglob('*.jsonl')))
    logger.info(f"找到 {len(files)} 个 .jsonl 文件。")
    return files








async def process_file(evaluator: GeminiEvaluator, input_path: Path, output_path: Path, batch_size: int, delay: float):
    logger.info(f"--- 处理文件: {input_path.name} ---")

    try:
        chunk_iterator = pd.read_json(input_path, lines=True, chunksize=batch_size)

        with open(output_path, 'w', encoding='utf-8') as f_out:
            for i, chunk in enumerate(chunk_iterator):
                logger.info(f"  - 批次 {i+1} 中的 {len(chunk)} 行数据...")

                tasks = []
                for _, row in chunk.iterrows():
                    source = row.get("source_text", "")
                    image_path = row.get("image_path", "")
                    tasks.append(evaluator.evaluate_pair(source, image_path))

                evaluations = await asyncio.gather(*tasks)

                for index, original_data in chunk.to_dict('index').items():
                    evaluation_result = evaluations[index % batch_size]
                    original_data["gemini_response"] = evaluation_result
                    f_out.write(json.dumps(original_data, ensure_ascii=False) + '\n')

                logger.info(f"  - 批次 {i+1} 完成 ✅")
                await asyncio.sleep(delay)

        logger.info(f"--- 完成文件处理: {output_path.name} ---")

    except Exception as e:
        logger.error(f"文件 {input_path.name} 出错: {e}", exc_info=True)









async def main():
    parser = argparse.ArgumentParser(description='图文问答评估器 - 使用Gemini处理图像+文字输入')
    parser.add_argument('-i', '--input-folder', default="my_corpus", help='输入文件夹,包含 .jsonl 文件')
    parser.add_argument('-o', '--output-folder', default="evaluated_output", help='输出文件夹')
    parser.add_argument('-k', '--api-key', help='API 密钥或使用 GEMINI_API_KEY 环境变量')
    parser.add_argument('-u', '--base-url', help='API Base URL')
    parser.add_argument('-m', '--model', default='gemini-2.5-flash-preview-05-20-nothinking', help='使用的模型名称')
    parser.add_argument('-b', '--batch-size', type=int, default=5, help='每批处理数量')
    parser.add_argument('-d', '--delay', type=float, default=1.0, help='批次之间的延迟秒数')
    args = parser.parse_args()

    api_key = args.api_key or os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.error("❌ 缺少 API Key！请使用 --api-key 或设置 GEMINI_API_KEY 环境变量。")
        return

    output_dir = Path(args.output_folder)
    output_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    try:
        files = get_jsonl_files(args.input_folder)
        if not files:
            return

        async with GeminiEvaluator(api_key, args.base_url, args.model) as evaluator:
            for input_file in files:
                output_file = output_dir / f"{input_file.stem}_evaluated.jsonl"
                await process_file(evaluator, input_file, output_file, args.batch_size, args.delay)

    except Exception as e:
        logger.error(f"主任务异常: {e}")
    finally:
        end_time = time.time()
        logger.info(f"🎉 所有任务完成,用时 {end_time - start_time:.2f} 秒。")


if __name__ == "__main__":
    asyncio.run(main()) 
