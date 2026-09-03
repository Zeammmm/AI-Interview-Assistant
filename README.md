# AI Interview Assistant

基于 **DeepSeek + RAG + Gradio** 的本地智能面试准备与模拟训练工具。它将公司存档、岗位 JD、个人简历与本地知识库结合起来，帮助用户准备技术面试、进行多轮模拟，并获得可执行的回答改进建议。

> 当前版本：V1 — RAG 知识库与模拟面试闭环已可用。

## 功能概览

### 面试准备

- 保存、读取和删除公司 / 岗位 / JD 存档
- 根据公司、岗位、JD 与知识库生成针对性面试题
- 为单题生成专业解释与口语化回答
- 收藏题目，方便后续复习

### 我的知识库（RAG）

- 支持上传 `.txt`、`.md`、`.pdf` 文件
- 普通 PDF 优先读取文本层；扫描版 PDF 自动使用 EasyOCR
- 文本按 Chunk 切分后生成中文向量索引
- 在生成题目、回答及模拟面试时检索相关知识
- 索引与 OCR 中间结果保存在本地，不调用大模型 Token

### 模拟面试

- 根据岗位、JD、简历、面试模式和知识库生成首题
- 回答后给出评分与维度评价：专业准确性、表达清晰度、岗位匹配度、项目结合度
- 明确列出优点、待改进点与可执行建议
- 生成“如果我是你，我会这样回答”的参考版本
- 回答“不会 / 不知道 / 没接触过”等内容时进入教学模式，先讲解再给简化追问
- 支持跳题与整场面试复盘

## 项目流程

```text
知识库文件
  ↓
文本提取 / OCR
  ↓
Chunk 切分
  ↓
本地 Embedding 与向量索引
  ↓
RAG 检索
  ↓
DeepSeek 生成题目、回答、评分与复盘
```

## 项目结构

```text
AI-Interview-Assistant/
├── app.py                 # Gradio 页面与业务流程
├── api.py                 # DeepSeek 调用封装
├── prompt.py              # 面试准备、模拟面试提示词
├── document_reader.py     # TXT / MD / PDF / OCR 文本读取
├── text_splitter.py       # 文本 Chunk 切分
├── rag.py                 # 文档缓存、索引构建与 RAG 上下文
├── vector_store.py        # 本地向量索引与相似度检索
├── knowledge_loader.py    # 知识库文件管理
├── storage.py             # 公司存档与收藏管理
├── knowledge/interview/   # 本地知识库文件（不建议上传 Git）
├── data/                  # 本地索引、缓存与用户数据（不建议上传 Git）
├── requirements.txt
└── README.md
```

## 安装与运行

推荐 Python 3.11。

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

在项目根目录创建 `.env`：

```text
DEEPSEEK_API_KEY=你的 DeepSeek API Key
```

启动应用：

```powershell
python app.py
```

浏览器打开：

```text
http://127.0.0.1:7860
```

## 首次使用

1. 在“我的知识库”上传学习笔记、面试题或项目经历资料。
2. 点击“重新构建 RAG 索引”。首次构建会读取 PDF、必要时执行 OCR，因此耗时取决于资料数量。
3. 在“面试准备”保存公司、岗位和 JD，生成针对性题目。
4. 在“模拟面试”选择公司并填写岗位 / JD，可选上传简历，然后开始面试。

## 隐私与 Git

`.env`、`knowledge/` 和 `data/` 可能包含 API Key、个人简历、知识库或本地索引，应通过 `.gitignore` 排除，GitHub 仓库建议设置为 Private。

## 后续计划

- 上传、删除知识库时只增量更新对应索引
- 将真实项目经历自动用于“项目举例”模块
- 增加模拟面试历史记录与按题复习
- 支持更丰富的简历格式和面试报告导出
