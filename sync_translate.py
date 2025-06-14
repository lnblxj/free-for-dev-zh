import requests
import json
import re
import time
import os

# 获取源仓库README.md内容
source_url = "https://raw.githubusercontent.com/ripienaar/free-for-dev/master/README.md"
response = requests.get(source_url)
if response.status_code != 200:
    print(f"Failed to fetch source README: {response.status_code}")
    exit(1)
    
source_content = response.text
print(f"Successfully fetched source README: {len(source_content)} characters")

# 分片处理，每片10000字符
chunk_size = 10000
chunks = []

# 保留原始标题和开头部分不翻译
header_match = re.search(r"^([\s\S]*?)(## Table of Contents|## 目录)", source_content)
if header_match:
    header = header_match.group(1)
    main_content = source_content[len(header):]
    
    # 将header单独作为一个chunk
    chunks.append(header)
    
    # 分割主要内容
    for i in range(0, len(main_content), chunk_size):
        chunks.append(main_content[i:i+chunk_size])
else:
    # 如果没找到标题模式，就直接分片
    for i in range(0, len(source_content), chunk_size):
        chunks.append(source_content[i:i+chunk_size])

print(f"Split content into {len(chunks)} chunks")

# 翻译函数
def translate_chunk(chunk, index):
    print(f"Translating chunk {index+1}/{len(chunks)}...")
    
    # 构建翻译提示
    prompt = f"""请将以下GitHub仓库README.md内容翻译成中文。这是一个名为free-for-dev的仓库，收集了对开发者免费的服务列表。
    
    翻译规则：
    1. 保留所有链接、代码、标记符号不变
    2. 保留所有专业术语和专有名词的原文，可以在首次出现时在括号中给出中文解释
    3. 保持Markdown格式不变
    4. 翻译要准确、专业、通顺
    5. 不要添加原文中没有的内容
    
    以下是需要翻译的内容：
    
    {chunk}
    """
    
    # 调用AI网关
    gateway_url = os.environ.get("AI_GATEWAY_URL")
    if not gateway_url:
        print("Error: AI_GATEWAY_URL not found in environment variables")
        exit(1)
        
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = requests.post(
                gateway_url,
                headers=headers,
                json=data,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                translated_text = result["candidates"][0]["content"]["parts"][0]["text"]
                return translated_text
            else:
                print(f"API request failed with status code {response.status_code}: {response.text}")
                retry_count += 1
                time.sleep(5)  # 等待5秒后重试
        except Exception as e:
            print(f"Error during API request: {str(e)}")
            retry_count += 1
            time.sleep(5)  # 等待5秒后重试
    
    print(f"Failed to translate chunk {index+1} after {max_retries} attempts")
    return chunk  # 如果翻译失败，返回原文

# 翻译所有分片
translated_chunks = []

# 第一个chunk（标题部分）不翻译，直接添加
translated_chunks.append(chunks[0])

# 翻译其余分片
for i in range(1, len(chunks)):
    translated_chunk = translate_chunk(chunks[i], i)
    translated_chunks.append(translated_chunk)
    time.sleep(2)  # 添加延迟，避免API请求过于频繁

# 合并翻译结果
translated_content = "".join(translated_chunks)

# 保存翻译后的README.md
with open("README.md", "w", encoding="utf-8") as f:
    f.write(translated_content)
    
print("Translation completed and saved to README.md")