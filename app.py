import gradio as gr
import json
from storage import (
    save_company,
    load_companies,
    get_company,
    delete_company,
    save_favorite,
    load_favorites,
    get_favorite,
    delete_favorite
)
from knowledge_loader import (
    add_knowledge_files,
    load_knowledge_files,
    delete_knowledge_file
)
from api import call_deepseek
from rag import build_rag_context, rebuild_rag_index
from document_reader import read_document

from prompt import (
    build_interview_questions_prompt,
    build_question_detail_prompt,
    build_mock_opening_prompt,
    build_mock_evaluation_prompt,
    build_mock_skip_prompt,
    build_mock_teaching_prompt,
    build_mock_review_prompt
)

def get_knowledge_status():
    file_rows = load_knowledge_files()

    if not file_rows:
        return "当前知识库为空。"

    return f"当前知识库共有 {len(file_rows)} 个文件。"


def handle_rebuild_rag():
    try:
        chunk_count, errors = rebuild_rag_index()
    except Exception as exc:
        return f"RAG 索引构建失败：{exc}"

    message = f"RAG 索引构建完成，共 {chunk_count} 个文本块。"
    if errors:
        message += "\n\n跳过的文件：\n" + "\n".join(errors)
    return message

def handle_add_knowledge(files):
    """
    把上传文件加入本地知识库，
    然后刷新文件列表。
    """

    success_count, messages = add_knowledge_files(files)

    file_rows = load_knowledge_files()

    status_text = "\n".join(messages)

    status_text += (
        f"\n\n当前知识库共有 "
        f"{len(file_rows)} 个文件。"
    )

    if success_count > 0:
        gr.Info(
            f"成功加入 {success_count} 个知识库文件"
        )

    return (
        file_rows,
        status_text
    )
def handle_save_company(company_name, target_job, interview_date, jd):
    success, message = save_company(
        company_name,
        target_job,
        interview_date,
        jd
    )

    companies = load_companies()

    selected_company = company_name.strip() if success else None

    return (
        gr.update(
            choices=companies,
            value=selected_company
        ),
        gr.update(
            choices=companies,
            value=selected_company
        ),
        message
    )


def handle_load_company(company_name):
    company = get_company(company_name)

    if company is None:
        return "", "", "", ""

    return (
        company.get("company_name", ""),
        company.get("target_job", ""),
        company.get("interview_date", ""),
        company.get("jd", "")
    )

def handle_load_mock_company(company_name):
    company = get_company(company_name)

    if company is None:
        return "", ""

    return (
        company.get("target_job", ""),
        company.get("jd", "")
    )

def handle_delete_company(company_name):
    success, message = delete_company(company_name)

    companies = load_companies()

    return (
        gr.update(
            choices=companies,
            value=None
        ),
        gr.update(
            choices=companies,
            value=None
        ),
        "",
        "",
        "",
        "",
        message
    )
def handle_generate_questions(
    company_name,
    target_job,
    jd,
    question_count
):
    """
    根据公司、岗位和 JD 调用 DeepSeek 生成面试题。
    """

    if not company_name:
        return (
            gr.update(
                choices=[],
                value=None
            ),
            {}
        )
    if not target_job:
        return (
            gr.update(
                choices=[],
                value=None
            ),
            {}
        )
    if not jd:
        return (
            gr.update(
                choices=[],
                value=None
            ),
            {}
        )


    rag_context = build_rag_context(
        f"{target_job}\n{jd}"
    )

    prompt = build_interview_questions_prompt(
        company_name,
        target_job,
        jd,
        int(question_count),
        rag_context
    )

    result = call_deepseek(prompt)

    questions = []

    for line in result.splitlines():

        line = line.strip()

        if not line:
            continue

        if ". " in line:
            question = line.split(". ", 1)[1].strip()
        else:
            question = line

        if question:
            questions.append(question)

    numbered_questions = []

    for index, question in enumerate(questions, start=1):
        numbered_question = f"{index}. {question}"
        numbered_questions.append(numbered_question)

    return (
        gr.update(
            choices=numbered_questions,
            value=numbered_questions[0] if numbered_questions else None
        ),
        {}
    )


def handle_select_question(question, answer_cache):
    """
    切换题目时：
    1. 不调用 DeepSeek
    2. 只更新当前题目
    3. 如果缓存里已有答案，就直接显示
    """

    if not question:
        return (
            "",
            "暂未生成答案。",
            "暂未生成答案。",
            "暂未生成答案。"
        )

    cached_answer = answer_cache.get(question)

    if cached_answer:
        return (
            question,
            cached_answer.get(
                "professional_answer",
                "暂无专业解释。"
            ),
            cached_answer.get(
                "simple_answer",
                "暂无口语化回答。"
            ),
            cached_answer.get(
                "project_example",
                "暂无项目举例。"
            )
        )

    return (
        question,
        "暂未生成答案，请点击“✨ 获取答案”。",
        "暂未生成答案，请点击“✨ 获取答案”。",
        "暂未生成答案，请点击“✨ 获取答案”。"
    )

def handle_get_answer(
    question,
    company_name,
    target_job,
    jd,
    answer_cache
):
    """
    获取当前题目的答案。

    如果缓存中已有答案：
        直接返回缓存

    如果没有：
        调用 DeepSeek 生成，并写入缓存
    """

    if not question:
        return (
            "请先选择一道题。",
            "",
            "",
            answer_cache
        )

    cached_answer = answer_cache.get(question)

    if cached_answer:
        return (
            cached_answer.get(
                "professional_answer",
                "暂无专业解释。"
            ),
            cached_answer.get(
                "simple_answer",
                "暂无口语化回答。"
            ),
            cached_answer.get(
                "project_example",
                "暂无项目举例。"
            ),
            answer_cache
        )

    rag_context = build_rag_context(
        f"{target_job}\n{question}"
    )

    prompt = build_question_detail_prompt(
        company_name,
        target_job,
        jd,
        question,
        rag_context
    )

    result = call_deepseek(prompt)

    result = result.strip()

    if result.startswith("```json"):
        result = result[7:]
    elif result.startswith("```"):
        result = result[3:]

    if result.endswith("```"):
        result = result[:-3]

    result = result.strip()

    try:
        detail = json.loads(result)

    except json.JSONDecodeError:
        return (
            "AI 返回内容解析失败，请重新点击获取答案。",
            "",
            "",
            answer_cache
        )

    professional_answer = detail.get(
        "professional_answer",
        "暂无专业解释。"
    )

    simple_answer = detail.get(
        "simple_answer",
        "暂无口语化回答。"
    )

    project_example = "真实项目完善后再补充。"

    answer_cache[question] = {
        "professional_answer": professional_answer,
        "simple_answer": simple_answer,
        "project_example": project_example
    }

    return (
        professional_answer,
        simple_answer,
        project_example,
        answer_cache
    )
def handle_save_favorite(
    question,
    company_name,
    target_job,
    answer_cache
):
    """
    收藏当前题目以及已经生成的答案。
    """

    if not question:
        gr.Warning("请先选择一道题目。")

        return (
            "⚠️ 请先选择一道题目。",
            gr.update()
        )

    cached_answer = answer_cache.get(question)

    if not cached_answer:
        gr.Warning("请先点击“获取答案”，再收藏这道题。")

        return (
            "⚠️ 请先生成当前题目的答案。",
            gr.update()
        )

    professional_answer = cached_answer.get(
        "professional_answer",
        ""
    )

    simple_answer = cached_answer.get(
        "simple_answer",
        ""
    )

    project_example = cached_answer.get(
        "project_example",
        ""
    )

    success, message = save_favorite(
        question,
        professional_answer,
        simple_answer,
        project_example,
        company_name,
        target_job
    )

    if not success:
        gr.Warning(message)

        return (
            f"⚠️ {message}",
            gr.update()
        )

    gr.Info("收藏成功")

    favorites = load_favorites()

    favorite_choices = []

    for favorite in favorites:
        favorite_id = favorite.get("id", "")
        favorite_question = favorite.get("question", "")

        favorite_choices.append(
            f"{favorite_id} | {favorite_question}"
        )

    return (
        f"✅ {message}",
        gr.update(
            choices=favorite_choices
        )
    )
def handle_remove_favorite(choice):
    """
    删除当前选择的收藏题目，
    并刷新收藏列表、清空右侧详情。
    """

    favorite_id = extract_favorite_id(choice)

    if not favorite_id:
        gr.Warning("请先选择要取消收藏的题目。")

        return (
            gr.update(),
            "## 请选择一道收藏题目",
            "暂无内容",
            "暂无内容",
            "暂无内容",
            "",
            "",
            ""
        )

    success, message = delete_favorite(favorite_id)

    if not success:
        gr.Warning(message)

        return (
            gr.update(),
            "## 请选择一道收藏题目",
            "暂无内容",
            "暂无内容",
            "暂无内容",
            "",
            "",
            ""
        )

    gr.Info("已取消收藏")

    new_choices = build_favorite_choices()

    return (
        gr.update(
            choices=new_choices,
            value=None
        ),
        "## 请选择一道收藏题目",
        "暂无内容",
        "暂无内容",
        "暂无内容",
        "",
        "",
        ""
    )
def build_favorite_choices():
    favorites = load_favorites()

    choices = []

    for favorite in favorites:
        favorite_id = favorite.get("id", "")
        question = favorite.get("question", "")

        choices.append(
            f"{favorite_id} | {question}"
        )

    return choices
def extract_favorite_id(choice):
    """
    从收藏列表显示文字中提取收藏 ID。

    例如：
    "0001 | 什么是RAG？"
    ↓
    "0001"
    """

    if not choice:
        return None

    return choice.split(" | ", 1)[0].strip()
def handle_load_favorite(choice):
    """
    点击收藏题目后，加载右侧完整详情。
    """

    favorite_id = extract_favorite_id(choice)

    if not favorite_id:
        return (
            "## 请选择一道收藏题目",
            "暂无内容",
            "暂无内容",
            "暂无内容",
            "",
            "",
            ""
        )

    favorite = get_favorite(favorite_id)

    if favorite is None:
        return (
            "## 收藏题目不存在",
            "暂无内容",
            "暂无内容",
            "暂无内容",
            "",
            "",
            ""
        )

    question = favorite.get("question", "")
    professional_answer = favorite.get(
        "professional_answer",
        "暂无内容"
    )
    simple_answer = favorite.get(
        "simple_answer",
        "暂无内容"
    )
    project_example = favorite.get(
        "project_example",
        "暂无内容"
    )
    company_name = favorite.get("company_name", "")
    target_job = favorite.get("target_job", "")
    favorite_time = favorite.get("favorite_time", "")

    return (
        f"## {question}",
        professional_answer,
        simple_answer,
        project_example,
        company_name,
        target_job,
        favorite_time
    )

def handle_select_knowledge_file(file_rows, evt: gr.SelectData):
    """
    用户点击知识库表格中的某个位置时，
    获取这一行对应的文件名。
    """

    if not file_rows:
        return ""

    row_index = evt.index[0]

    if row_index >= len(file_rows):
        return ""

    file_name = file_rows[row_index][0]

    return file_name
def handle_delete_knowledge(file_name):
    """
    删除选中的知识库文件，
    然后刷新知识库列表和状态。
    """

    if not file_name:
        gr.Warning("请先点击选择一个知识库文件。")

        return (
            load_knowledge_files(),
            get_knowledge_status(),
            ""
        )

    success, message = delete_knowledge_file(file_name)

    if success:
        gr.Info(message)
    else:
        gr.Warning(message)

    file_rows = load_knowledge_files()

    status_text = (
        f"{message}\n\n"
        f"当前知识库共有 {len(file_rows)} 个文件。"
    )

    return (
        file_rows,
        status_text,
        ""
    )


def _read_resume(resume_file):
    if not resume_file:
        return ""

    file_path = getattr(resume_file, "name", resume_file)
    try:
        return read_document(file_path)[:6000]
    except Exception as exc:
        return f"简历读取失败：{exc}"


def _build_transcript(turns):
    return "\n\n".join(
        f"{'面试官' if item['role'] == 'interviewer' else '候选人'}：{item['content']}"
        for item in turns[-12:]
    )


def _clean_json(text):
    text = (text or "").strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)


def _format_evaluation(result):
    strengths = "\n".join(f"- {item}" for item in result.get("strengths", []))
    improvements = "\n".join(f"- {item}" for item in result.get("improvements", []))

    return f"""### 本题评分：{result.get('score', 0)} / 100

专业准确性：{result.get('professional_accuracy', 0)} ｜ 表达清晰度：{result.get('clarity', 0)} ｜ 岗位匹配度：{result.get('job_match', 0)} ｜ 项目结合：{result.get('project_connection', 0)}

**做得好的地方**
{strengths or '- 暂无'}

**可以改进的地方**
{improvements or '- 暂无'}

**如果我是你，我会这样回答**
{result.get('better_answer', '暂无示范回答。')}

**下一题**
{result.get('next_question', '请继续补充刚才的回答。')}"""


def _is_unsure_answer(answer):
    normalized = "".join((answer or "").lower().split())
    unsure_phrases = (
        "不会", "不知道", "不了解", "没学过", "没接触过",
        "没接触", "没想过", "没思考过", "不太会", "答不上来",
        "想不起来", "不清楚", "不懂", "idk", "don'tknow", "donotknow",
    )
    return len(normalized) < 4 or any(item in normalized for item in unsure_phrases)


def _format_teaching(result):
    framework = "\n".join(
        f"{index}. {item}"
        for index, item in enumerate(result.get("answer_framework", []), start=1)
    )
    key_points = "\n".join(f"- {item}" for item in result.get("key_points", []))
    default_framework = "1. 先说核心结论\n2. 再解释原因\n3. 最后补充场景"
    framework = framework or default_framework

    return f"""### 这题先不评分，我们先把它学会

**核心思路**
{result.get('topic_explanation', '暂无讲解。')}

**回答框架**
{framework}

**你可以这样回答**
{result.get('better_answer', '暂无推荐回答。')}

**记住这几点**
{key_points or '- 暂无'}

**练习追问**
{result.get('next_question', '请用自己的话复述刚才的核心思路。')}"""


def handle_start_mock(company_name, target_job, resume_file, jd, interview_style):
    if not target_job or not jd:
        return [], {}, "", "请先填写应聘岗位和招聘 JD。"

    resume = _read_resume(resume_file)
    rag_context = build_rag_context(f"{target_job}\n{jd}")
    prompt = build_mock_opening_prompt(
        company_name, target_job, jd, interview_style, resume, rag_context
    )
    opening = call_deepseek(prompt).strip()
    if not opening:
        opening = "面试开始。请先介绍一下你与这个岗位最相关的经历。"

    state = {
        "company_name": company_name,
        "target_job": target_job,
        "jd": jd,
        "interview_style": interview_style,
        "resume": resume,
        "turns": [{"role": "interviewer", "content": opening}],
    }
    return [(None, opening)], state, "", "面试已开始。请回答第一题。"


def handle_submit_mock_answer(answer, state, chat_history):
    if not state or not state.get("turns"):
        return chat_history or [], state or {}, "", "请先点击“开始模拟面试”。"
    if not answer or not answer.strip():
        return chat_history, state, "请输入你的回答。", ""

    answer = answer.strip()
    turns = state["turns"]
    turns.append({"role": "candidate", "content": answer})
    transcript = _build_transcript(turns)
    rag_context = build_rag_context(
        f"{state['target_job']}\n{turns[-2]['content']}"
    )

    try:
        if _is_unsure_answer(answer):
            prompt = build_mock_teaching_prompt(
                state["target_job"], state["jd"], rag_context, transcript
            )
            teaching = _clean_json(call_deepseek(prompt))
            feedback = _format_teaching(teaching)
            next_question = teaching.get(
                "next_question", "请用自己的话复述刚才的核心思路。"
            )
        else:
            prompt = build_mock_evaluation_prompt(
                state["target_job"], state["jd"], state["interview_style"],
                state["resume"], rag_context, transcript
            )
            evaluation = _clean_json(call_deepseek(prompt))
            feedback = _format_evaluation(evaluation)
            next_question = evaluation.get(
                "next_question", "请继续补充刚才的回答。"
            )
    except (json.JSONDecodeError, TypeError, ValueError):
        feedback = "本题讲解或评价生成失败，请重新提交一次。"
        next_question = ""

    if next_question:
        turns.append({"role": "interviewer", "content": next_question})
    state["turns"] = turns
    history = list(chat_history or []) + [(answer, feedback)]
    return history, state, "", ""


def handle_skip_mock_question(state, chat_history):
    if not state or not state.get("turns"):
        return chat_history or [], state or {}, "请先点击“开始模拟面试”。"

    turns = state["turns"]
    turns.append({"role": "candidate", "content": "（已跳过此题）"})
    transcript = _build_transcript(turns)
    rag_context = build_rag_context(f"{state['target_job']}\n{state['jd']}")
    prompt = build_mock_skip_prompt(
        state["target_job"], state["jd"], state["interview_style"],
        state["resume"], rag_context, transcript
    )
    next_question = call_deepseek(prompt).strip()
    if not next_question:
        next_question = "请介绍一个你最有代表性的项目，并说明你负责的部分。"

    turns.append({"role": "interviewer", "content": next_question})
    state["turns"] = turns
    history = list(chat_history or []) + [("（跳过此题）", next_question)]
    return history, state, ""


def handle_end_mock(state):
    if not state or not state.get("turns"):
        return "请先开始一场模拟面试。"

    transcript = _build_transcript(state["turns"])
    if len(state["turns"]) < 3:
        return "至少回答一道题后再生成复盘。"

    prompt = build_mock_review_prompt(
        state["target_job"], state["jd"], state["interview_style"], transcript
    )
    return call_deepseek(prompt)


with gr.Blocks(title="AI Interview Assistant") as demo:

    gr.Markdown(
        """
        # AI Interview Assistant
        ### 智能面试准备与模拟训练系统

        根据公司、岗位、招聘 JD、个人简历和自定义题库，
        提供针对性面试准备、真实模拟面试、收藏复习与 RAG 知识库管理。
        """
    )
    answer_cache = gr.State({})
    selected_knowledge_file = gr.State("")
    interview_state = gr.State({})
    with gr.Tabs():

        # ==================================================
        # 1. 面试准备
        # ==================================================
        with gr.Tab("🏢 面试准备"):

            with gr.Row():

                # ---------------------------
                # 左侧：公司存档
                # ---------------------------
                with gr.Column(scale=1):

                    gr.Markdown("## 公司存档")

                    company_list = gr.Dropdown(
                        label="选择公司",
                        choices=load_companies(),
                        interactive=True
                    )

                    company_name = gr.Textbox(
                        label="公司名称",
                        placeholder="例如：XX科技有限公司"
                    )

                    target_job = gr.Textbox(
                        label="应聘岗位",
                        placeholder="例如：AI应用开发工程师"
                    )

                    interview_date = gr.Textbox(
                        label="面试时间",
                        placeholder="例如：2026-09-05 14:00"
                    )

                    jd_input = gr.Textbox(
                        label="招聘 JD",
                        placeholder="粘贴岗位职责和任职要求",
                        lines=12
                    )

                    with gr.Row():

                        save_company_btn = gr.Button(
                            "💾 保存公司",
                            variant="primary"
                        )

                        delete_company_btn = gr.Button(
                            "删除公司"
                        )
                    company_status = gr.Textbox(
                        label="存档状态",
                        interactive=False
                    )
                # ---------------------------
                # 右侧：题库训练
                # ---------------------------
                with gr.Column(scale=2):

                    gr.Markdown("## 针对性面试准备")

                    gr.Markdown(
                        """
                        系统会根据 **公司 + 岗位 + JD + 知识库**
                        自动检索相关面试知识并生成针对性题目。
                        """
                    )

                    with gr.Row():

                        question_count = gr.Slider(
                            minimum=1,
                            maximum=20,
                            value=5,
                            step=1,
                            label="生成题目数量"
                        )

                        generate_btn = gr.Button(
                            "✨ 生成针对性面试题",
                            variant="primary"
                        )

                    question_selector = gr.Radio(
                        label="本次生成的面试题",
                        choices=[],
                        interactive=True
                    )

                    current_question = gr.Textbox(
                        label="当前题目",
                        lines=3,
                        interactive=False
                    )
                    get_answer_btn = gr.Button(
                        "✨ 获取答案",
                        variant="primary"
                    )
                    with gr.Tabs():

                        with gr.Tab("📘 专业解释"):

                            professional_answer = gr.Markdown(
                                "生成题目后，这里显示完整、专业的技术解释。"
                            )

                        with gr.Tab("🗣️ 口语化回答"):

                            simple_answer = gr.Markdown(
                                "这里生成更适合你在真实面试中表达的回答。"
                            )

                        with gr.Tab("💡 项目举例"):

                            example_answer = gr.Markdown(
                                "这里尽量结合你的真实项目经历举例。"
                            )

                    with gr.Row():

                        favorite_btn = gr.Button(
                            "⭐ 收藏当前题目"
                        )
                        favorite_status = gr.Markdown("")

        # ==================================================
        # 2. 模拟面试
        # ==================================================
        with gr.Tab("🎤 模拟面试"):

            gr.Markdown(
                """
                ## 真实模拟面试

                AI 会结合你的简历、目标公司、岗位、JD 和题库进行多轮面试。
                它会根据你的回答动态追问，而不是简单按照固定题库依次提问。
                """
            )

            with gr.Row():

                # 左侧：面试设置
                with gr.Column(scale=1):

                    mock_company = gr.Dropdown(
                        label="面试公司",
                        choices=load_companies(),
                        interactive=True
                    )
                    mock_job = gr.Textbox(
                        label="面试岗位",
                        placeholder="例如：AI应用开发工程师"
                    )

                    resume_file = gr.File(
                        label="上传个人简历",
                        file_types=[".pdf"]
                    )

                    mock_jd = gr.Textbox(
                        label="招聘 JD",
                        lines=8,
                        placeholder="粘贴公司招聘 JD"
                    )

                    interview_style = gr.Radio(
                        choices=[
                            "综合面试",
                            "技术深挖",
                            "项目追问",
                            "基础八股"
                        ],
                        value="综合面试",
                        label="面试模式"
                    )

                    start_mock_btn = gr.Button(
                        "🎤 开始模拟面试",
                        variant="primary"
                    )

                    end_mock_btn = gr.Button(
                        "结束并生成复盘"
                    )

                # 右侧：聊天式模拟面试
                with gr.Column(scale=2):

                    interview_chat = gr.Chatbot(
                        label="模拟面试对话",
                        height=500
                    )

                    user_answer = gr.Textbox(
                        label="你的回答",
                        placeholder="输入你的回答...",
                        lines=4
                    )

                    with gr.Row():

                        submit_answer_btn = gr.Button(
                            "提交回答",
                            variant="primary"
                        )

                        skip_question_btn = gr.Button(
                            "跳过这题"
                        )

                    with gr.Accordion(
                        "面试复盘",
                        open=False
                    ):

                        interview_review = gr.Markdown(
                            "结束面试后，这里会显示整体评价、薄弱点和改进建议。"
                        )

        # ==================================================
        # 3. 收藏题库
        # ==================================================
        with gr.Tab("⭐ 收藏题库"):

            gr.Markdown(
                """
                ## 我的收藏题库

                收藏高频题、不会的题以及需要反复复习的题目。
                """
            )

            with gr.Row():

                # ---------------------------
                # 左侧：搜索 + 可滚动题目列表
                # ---------------------------
                with gr.Column(scale=1):

                    favorite_search = gr.Textbox(
                        label="搜索收藏题目",
                        placeholder="输入关键词，例如：RAG / FastAPI / Prompt"
                    )

                    favorite_question_list = gr.Radio(
                        label="收藏题目",
                        choices=build_favorite_choices(),
                        interactive=True
                    )

                    remove_favorite_btn = gr.Button(
                        "取消收藏"
                    )

                # ---------------------------
                # 右侧：详情
                # ---------------------------
                with gr.Column(scale=2):

                    favorite_question = gr.Markdown(
                        "## 请选择一道收藏题目"
                    )

                    with gr.Tabs():

                        with gr.Tab("📘 专业解释"):

                            favorite_professional_answer = gr.Markdown(
                                "暂无内容"
                            )

                        with gr.Tab("🗣️ 口语化回答"):

                            favorite_simple_answer = gr.Markdown(
                                "暂无内容"
                            )

                        with gr.Tab("💡 项目举例"):

                            favorite_example = gr.Markdown(
                                "暂无内容"
                            )

                    with gr.Accordion(
                        "题目来源信息",
                        open=False
                    ):

                        favorite_company = gr.Textbox(
                            label="所属公司",
                            interactive=False
                        )

                        favorite_job = gr.Textbox(
                            label="对应岗位",
                            interactive=False
                        )

                        favorite_time = gr.Textbox(
                            label="收藏时间",
                            interactive=False
                        )

        # ==================================================
        # 4. 我的知识库
        # ==================================================
        with gr.Tab("📚 我的知识库"):

            gr.Markdown(
                """
                ## 面试知识库

                上传你自己的八股文、面试题、学习笔记等资料。
                系统后续会自动建立 RAG 索引并从全部知识库中检索相关内容。
                """
            )

            with gr.Row():

                with gr.Column(scale=1):

                    knowledge_files = gr.File(
                        label="上传知识库文件",
                        file_count="multiple",
                        file_types=[".txt", ".md", ".pdf"]
                    )

                    add_knowledge_btn = gr.Button(
                        "📚 加入知识库",
                        variant="primary"
                    )

                with gr.Column(scale=2):
                    uploaded_files = gr.Dataframe(
                        headers=[
                            "文件名",
                            "类型",
                            "加入时间"
                        ],
                        datatype=[
                            "str",
                            "str",
                            "str"
                        ],
                        value=load_knowledge_files(),
                        type="array",
                        label="已加入知识库的文件",
                        interactive=False
                    )

                    delete_knowledge_btn = gr.Button(
                        "删除选中文件"
                    )

                    rebuild_rag_btn = gr.Button(
                        "重新构建 RAG 索引"
                    )

            with gr.Accordion(
                "知识库状态",
                open=True
            ):
                knowledge_status = gr.Textbox(
                    value=get_knowledge_status(),
                    lines=5,
                    interactive=False
                )
    # =========================
    # 公司存档事件绑定
    # =========================

    save_company_btn.click(
        fn=handle_save_company,
        inputs=[
            company_name,
            target_job,
            interview_date,
            jd_input
        ],
        outputs=[
            company_list,
            mock_company,
            company_status
        ]
    )

    company_list.change(
        fn=handle_load_company,
        inputs=[
            company_list
        ],
        outputs=[
            company_name,
            target_job,
            interview_date,
            jd_input
        ]
    )
    mock_company.change(
        fn=handle_load_mock_company,
        inputs=[
            mock_company
        ],
        outputs=[
            mock_job,
            mock_jd
        ]
    )
    start_mock_btn.click(
        fn=handle_start_mock,
        inputs=[
            mock_company,
            mock_job,
            resume_file,
            mock_jd,
            interview_style
        ],
        outputs=[
            interview_chat,
            interview_state,
            user_answer,
            interview_review
        ]
    )
    submit_answer_btn.click(
        fn=handle_submit_mock_answer,
        inputs=[
            user_answer,
            interview_state,
            interview_chat
        ],
        outputs=[
            interview_chat,
            interview_state,
            user_answer,
            interview_review
        ]
    )
    user_answer.submit(
        fn=handle_submit_mock_answer,
        inputs=[
            user_answer,
            interview_state,
            interview_chat
        ],
        outputs=[
            interview_chat,
            interview_state,
            user_answer,
            interview_review
        ]
    )
    skip_question_btn.click(
        fn=handle_skip_mock_question,
        inputs=[
            interview_state,
            interview_chat
        ],
        outputs=[
            interview_chat,
            interview_state,
            interview_review
        ]
    )
    end_mock_btn.click(
        fn=handle_end_mock,
        inputs=[interview_state],
        outputs=[interview_review]
    )
    delete_company_btn.click(
        fn=handle_delete_company,
        inputs=[
            company_list
        ],
        outputs=[
            company_list,
            mock_company,
            company_name,
            target_job,
            interview_date,
            jd_input,
            company_status
        ]
    )
    generate_btn.click(
        fn=handle_generate_questions,
        inputs=[
            company_name,
            target_job,
            jd_input,
            question_count
        ],
        outputs=[
            question_selector,
            answer_cache
        ]
    )

    question_selector.change(
        fn=handle_select_question,
        inputs=[
            question_selector,
            answer_cache
        ],
        outputs=[
            current_question,
            professional_answer,
            simple_answer,
            example_answer
        ]
    )
    get_answer_btn.click(
        fn=handle_get_answer,
        inputs=[
            current_question,
            company_name,
            target_job,
            jd_input,
            answer_cache
        ],
        outputs=[
            professional_answer,
            simple_answer,
            example_answer,
            answer_cache
        ]
    )
    favorite_btn.click(
        fn=handle_save_favorite,
        inputs=[
            current_question,
            company_name,
            target_job,
            answer_cache
        ],
        outputs=[
            favorite_status,
            favorite_question_list
        ]
    )
    favorite_question_list.change(
        fn=handle_load_favorite,
        inputs=[
            favorite_question_list
        ],
        outputs=[
            favorite_question,
            favorite_professional_answer,
            favorite_simple_answer,
            favorite_example,
            favorite_company,
            favorite_job,
            favorite_time
        ]
    )
    remove_favorite_btn.click(
        fn=handle_remove_favorite,
        inputs=[
            favorite_question_list
        ],
        outputs=[
            favorite_question_list,
            favorite_question,
            favorite_professional_answer,
            favorite_simple_answer,
            favorite_example,
            favorite_company,
            favorite_job,
            favorite_time
        ]
    )
    add_knowledge_btn.click(
        fn=handle_add_knowledge,
        inputs=[
            knowledge_files
        ],
        outputs=[
            uploaded_files,
            knowledge_status
        ]
    )
    uploaded_files.select(
        fn=handle_select_knowledge_file,
        inputs=[
            uploaded_files
        ],
        outputs=[
            selected_knowledge_file
        ]
    )
    delete_knowledge_btn.click(
        fn=handle_delete_knowledge,
        inputs=[
            selected_knowledge_file
        ],
        outputs=[
            uploaded_files,
            knowledge_status,
            selected_knowledge_file
        ]
    )
    rebuild_rag_btn.click(
        fn=handle_rebuild_rag,
        outputs=[knowledge_status]
    )
if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        inbrowser=True
    )

