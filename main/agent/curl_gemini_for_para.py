#!/usr/bin/env python3
"""
平行语料质量评估器
使用Gemini API评估JSONL文件中的英-老平行语料质量。
"""
import os
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict
import time
import asyncio
import aiohttp
import pandas as pd

# --- 设置日志 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 使用上面设计的Prompt ---
EVALUATION_PROMPT_TEMPLATE = """
As an expert linguistic evaluator specializing in English/Chinese and Thai/Lao, your task is to meticulously assess the quality of a Thai/Lao translation based on its English/Chinese source text.

**Evaluation Criteria:**

1.  **Accuracy (ความแม่นยำ):** Does the Lao text accurately and completely convey the meaning, nuance, and intent of the English/Chinese source? Are there any omissions, additions, or mistranslations?
2.  **Fluency & Grammar (ความลื่นไหลและไวยากรณ์):** Is the Lao text grammatically correct? Does it sound natural and fluent to a native speaker? Is the phrasing awkward or unconventional?
3.  **Machine Translation (MT) Artifacts (ร่องรอยการแปลด้วยเครื่อง):** Does the translation show signs of being a raw, unedited machine translation? For example, overly literal translations, unnatural word choices, or grammatical structures that mimic English/Chinese too closely.

**Your Task:**
Based on the criteria above, provide your analysis in Simple Chinese and a final quality score for the following text pair.

**Source Text (English/Chinese):**
"{source_text}"

**Target Text (Thai/Lao):**
"{target_text}"

**Output Format:**
You MUST provide your response in a valid JSON object format, with no other text or explanations before or after the JSON block. The JSON object must contain the following keys:
- "evaluation_summary": A brief, one-sentence summary of the translation quality.
- "accuracy_critique": A detailed critique of the translation's accuracy.
- "fluency_critique": A detailed critique of the translation's fluency and grammar.
- "mt_suspicion_critique": Your assessment of whether it sounds like a machine translation and why.
- "quality_score": A single integer score from 1 to 10, where 1 is "Completely incorrect/unusable" and 10 is "Perfect, human-quality translation".
"""

class GeminiEvaluator:
    """使用Gemini API评估语料的处理器"""
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

    async def evaluate_pair(self, source_text: str, target_text: str) -> dict:
        """评估单个源-目标文本对"""
        if not source_text or not target_text:
            return {"error": "Source or target text is empty."}
        
        prompt = EVALUATION_PROMPT_TEMPLATE.format(source_text=source_text, target_text=target_text)
        
        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "response_format": {"type": "json_object"} # 尝试强制模型输出JSON
            }
            
            async with self.session.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=120) as response: # type: ignore
                if response.status == 200:
                    response_json = await response.json()
                    content = response_json['choices'][0]['message']['content']
                    try:
                        # 解析模型返回的JSON字符串
                        evaluation_data = json.loads(content)
                        logger.info(f"成功评估并打分: {evaluation_data.get('quality_score')}/10")
                        return evaluation_data
                    except json.JSONDecodeError:
                        logger.error(f"无法解析模型返回的JSON: {content}")
                        return {"error": "Failed to parse JSON response", "raw_response": content}
                else:
                    error_text = await response.text()
                    logger.error(f"API请求失败: {response.status} - {error_text}")
                    return {"error": f"API Error {response.status}", "details": error_text}
        except Exception as e:
            logger.error(f"评估时发生异常: {e}")
            return {"error": "Exception during evaluation", "details": str(e)}

def get_jsonl_files(folder_path: str) -> List[Path]:
    folder = Path(folder_path)
    if not folder.is_dir():
        raise FileNotFoundError(f"文件夹不存在: {folder_path}")
    files = sorted(list(folder.rglob('*.jsonl')))
    logger.info(f"在 '{folder_path}' 中找到 {len(files)} 个 .jsonl 文件。")
    return files

async def process_file(evaluator: GeminiEvaluator, input_path: Path, output_path: Path, batch_size: int, delay: float):
    logger.info(f"--- 📂 开始处理文件: {input_path.name} ---")
    
    try:
        # 使用pandas逐块读取，更稳健
        chunk_iterator = pd.read_json(input_path, lines=True, chunksize=batch_size)
        
        with open(output_path, 'w', encoding='utf-8') as f_out:
            for i, chunk in enumerate(chunk_iterator):
                logger.info(f"  - 正在处理批次 {i+1} (共 {len(chunk)} 行)...")
                
                tasks = []
                for _, row in chunk.iterrows():
                    source = row.get("source_text", "")
                    target = row.get("target_text", "")
                    tasks.append(evaluator.evaluate_pair(source, target))
                
                evaluations = await asyncio.gather(*tasks)
                
                # 合并原始数据和评估结果并写入文件
                for index, original_data in chunk.to_dict('index').items():
                    evaluation_result = evaluations[index % batch_size]
                    # 将评估结果合并到新字段 "gemini_evaluation" 中
                    original_data["gemini_evaluation"] = evaluation_result
                    f_out.write(json.dumps(original_data, ensure_ascii=False) + '\n')
                
                logger.info(f"  - 批次 {i+1} 处理完成并已写入。")
                await asyncio.sleep(delay)

        logger.info(f"--- ✅ 文件处理完成: {output_path.name} ---")

    except Exception as e:
        logger.error(f"处理文件 {input_path.name} 时发生严重错误: {e}", exc_info=True)


async def main():
    parser = argparse.ArgumentParser(description='使用Gemini API批量评估平行语料质量')
    parser.add_argument('-i', '--input-folder', required=True, help='包含.jsonl文件的输入文件夹路径')
    parser.add_argument('-o', '--output-folder', required=True, help='用于存放评估结果的输出文件夹路径')
    parser.add_argument('-k', '--api-key', help='API密钥 (或通过环境变量 GEMINI_API_KEY 设置)')
    parser.add_argument('-u', '--base-url', help='API基础URL (例如 OpenAI 兼容接口)')
    parser.add_argument('-m', '--model', default='gemini-2.5-flash-preview-05-20-nothinking', help='要使用的模型名称')
    parser.add_argument('-b', '--batch-size', type=int, default=10, help='并发处理的批大小')
    parser.add_argument('-d', '--delay', type=float, default=1.0, help='每批请求间的延迟(秒)')
    args = parser.parse_args()

    api_key = args.api_key or os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.error("❌ 必须提供API密钥! 请通过 --api-key 参数或 GEMINI_API_KEY 环境变量设置。")
        return

    # 创建输出文件夹
    output_dir = Path(args.output_folder)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    start_time = time.time()
    try:
        jsonl_files = get_jsonl_files(args.input_folder)
        if not jsonl_files:
            return

        async with GeminiEvaluator(api_key, args.base_url, args.model) as evaluator:
            for input_file in jsonl_files:
                # 定义输出文件名
                output_file = output_dir / f"{input_file.stem}_evaluated.jsonl"
                await process_file(evaluator, input_file, output_file, args.batch_size, args.delay)

    except Exception as e:
        logger.error(f"程序执行期间发生未捕获的错误: {e}")
    finally:
        end_time = time.time()
        logger.info(f"🚀 全部任务完成，总耗时: {end_time - start_time:.2f} 秒。")

if __name__ == "__main__":
    asyncio.run(main())
