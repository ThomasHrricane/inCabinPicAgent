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

给出图中一共有几排座位，一共多少个座位，给出各座位上人员与物品情况,一共有几个人，是否在站立，前排左是什么情况，前排右是什么情况，后排左是什么情况
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
        """更接近 GPT-4o 网页端的图像编码器：压缩图像并转为 Base64"""
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

                logger.debug(f"图像编码完成，base64 长度：{len(encoded)} 字符")
                return encoded

        except Exception as e:
            logger.error(f"图片处理失败: {e}")
            raise

    
    async def evaluate_pair(self, source_text: str, image_path: str):
        """评估图文输入对，增强为类似 ChatGPT 网页版风格"""
        if not source_text or not image_path or not os.path.exists(image_path):
            return {"error": "Source text 或图片路径为空/无效"}

        image_base64 = self.encode_image(image_path)

        # ✅ 新增：更接近 ChatGPT 的 system prompt
        system_prompt = (
    "You are a multimodal assistant that can precisely understand and interpret images along with instructions."
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
                        logger.warning("输出非标准 JSON，原始输出已返回。")
                        # evaluation_data = content
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
    #                         logger.info(f"图文任务成功，置信度评分: {evaluation_data.get('confidence')}/10")
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
    parser.add_argument('-i', '--input-folder', default="my_corpus", help='输入文件夹，包含 .jsonl 文件')
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
        logger.info(f"🎉 所有任务完成，用时 {end_time - start_time:.2f} 秒。")


if __name__ == "__main__":
    asyncio.run(main())
