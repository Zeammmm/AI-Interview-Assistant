import os

from dotenv import load_dotenv
from openai import OpenAI


# 读取 .env 文件
load_dotenv()

# 从环境变量读取 DeepSeek API Key
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)


def call_deepseek(prompt):
    """
    调用 DeepSeek API。

    参数：
    prompt: str
        发送给大模型的完整提示词。

    返回：
    str
        DeepSeek 返回的文本内容。
    """

    if not DEEPSEEK_API_KEY:
        raise ValueError(
            "没有检测到 DEEPSEEK_API_KEY，请检查 .env 文件。"
        )

    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[
            {
                "role": "system",
                "content": "你是一名专业的软件开发与AI方向技术面试官。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=800,
        temperature=0.3,
        stream=False
    )

    return response.choices[0].message.content