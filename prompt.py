def build_interview_questions_prompt(
    company_name,
    target_job,
    jd,
    question_count,
    rag_context=""
):
    """
    构建“生成针对性面试题”的 Prompt。
    """

    prompt = f"""
你现在是一名经验丰富的技术面试官。

请根据下面的公司、应聘岗位和招聘 JD，
为候选人生成有针对性的技术面试题。

【公司】
{company_name}

【应聘岗位】
{target_job}

【招聘 JD】
{jd}

【知识库参考资料】
{rag_context or "暂无，请仅根据岗位和 JD 生成。"}

【要求】

1. 一共生成 {question_count} 道题。
2. 题目必须尽量结合招聘 JD，而不是生成泛泛的通用题。
3. 优先考察岗位真正要求的技术能力。
4. 可以包含：
   - 基础知识
   - 技术原理
   - 项目经验
   - 实际问题排查
   - 场景设计
5. 难度适合应届生或初级开发工程师。
6. 每道题只输出题目本身。
7. 不要输出答案。
8. 不要输出解释。
9. 不要使用 Markdown。
10. 每道题单独一行。

输出格式必须严格如下：

1. 第一道题
2. 第二道题
3. 第三道题
"""

    return prompt


def build_question_detail_prompt(
    company_name,
    target_job,
    jd,
    question,
    rag_context=""
):
    """
    为单道面试题生成：
    1. 简洁专业解释
    2. 面试口语化回答
    """

    prompt = f"""
你是一名技术面试辅导老师。

请针对下面这道面试题，给候选人生成简洁、实用的学习和面试回答。

【公司】
{company_name}

【岗位】
{target_job}

【招聘 JD】
{jd}

【面试题】
{question}

【知识库参考资料】
{rag_context or "暂无，请根据通用知识回答。"}

请只生成以下两部分：

一、professional_answer

目标：帮助候选人快速理解这道题。

要求：
1. 控制在 200～350 字。
2. 不要写成长篇教程。
3. 优先解释这道题最核心的 3～5 个知识点。
4. 使用清晰的分点结构。
5. 如果涉及流程，用 1、2、3 的方式说明。
6. 不要展开与题目关系不大的知识。
7. 不要堆砌技术名词。

二、simple_answer

目标：候选人在真实面试中可以直接说。

要求：
1. 控制在 120～200 字。
2. 大约 40～60 秒能够说完。
3. 使用第一人称。
4. 表达自然，像真实面试交流，不像背书。
5. 回答结构清晰：
   - 先说核心观点
   - 再简单解释
   - 最后补充一个关键点
6. 不要长篇展开。

必须只返回合法 JSON。
不要输出 Markdown 代码块。
不要输出 JSON 以外的文字。

格式：

{{
    "professional_answer": "专业解释",
    "simple_answer": "口语化回答"
}}
"""

    return prompt


def build_mock_opening_prompt(company_name, target_job, jd, interview_style, resume, rag_context):
    return f"""
你是一名真实、友善但有标准的技术面试官。请开始一场模拟面试。

【公司】{company_name or "未填写"}
【岗位】{target_job}
【招聘 JD】{jd}
【面试模式】{interview_style}
【候选人简历】{resume or "未上传简历"}
【知识库参考】{rag_context or "暂无"}

要求：
1. 先用一句话说明将开始面试。
2. 然后只提出一道具体问题，不要给答案或评分。
3. 问题要匹配岗位、JD 和候选人经历；没有经历时从基础或项目场景切入。
4. 控制在 150 字以内。
"""


def build_mock_evaluation_prompt(target_job, jd, interview_style, resume, rag_context, transcript):
    return f"""
你是一名技术面试官。请评价候选人的最新回答，并继续进行下一轮面试。

【岗位】{target_job}
【JD】{jd}
【面试模式】{interview_style}
【候选人简历】{resume or "未上传简历"}
【知识库参考】{rag_context or "暂无"}
【已进行的面试记录】
{transcript}

严格只返回合法 JSON，不要 Markdown，不要额外文字：
{{
  "score": 0,
  "professional_accuracy": 0,
  "clarity": 0,
  "job_match": 0,
  "project_connection": 0,
  "strengths": ["具体优点 1", "具体优点 2"],
  "improvements": ["具体缺点及改进方法 1", "具体缺点及改进方法 2"],
  "better_answer": "基于候选人原回答改写的一段更好的回答，保留其已有正确内容，不能凭空捏造项目经历。",
  "next_question": "根据刚才回答提出的一道追问或下一题"
}}

评分范围都是 0 到 100。评价必须具体、可执行，避免空泛鼓励。better_answer 控制在 180 字以内。
"""


def build_mock_skip_prompt(target_job, jd, interview_style, resume, rag_context, transcript):
    return f"""
你是一名技术面试官。候选人跳过了上一题，请根据以下信息提出下一道更合适的面试题。

【岗位】{target_job}
【JD】{jd}
【面试模式】{interview_style}
【候选人简历】{resume or "未上传简历"}
【知识库参考】{rag_context or "暂无"}
【已进行的面试记录】
{transcript}

只输出一道问题，不要解释，不要评分，控制在 120 字以内。
"""


def build_mock_teaching_prompt(target_job, jd, rag_context, transcript):
    return f"""
候选人在模拟面试中明确表示不会回答当前问题。你是一名耐心的面试辅导老师：先帮助他学会，再让面试自然继续。

【岗位】{target_job}
【JD】{jd}
【知识库参考】{rag_context or "暂无，请使用可靠的通用知识"}
【面试记录】
{transcript}

严格只返回合法 JSON，不要 Markdown，不要额外文字：
{{
  "topic_explanation": "用通俗语言解释这题的核心概念，控制在 120 字以内。",
  "answer_framework": ["回答步骤 1", "回答步骤 2", "回答步骤 3"],
  "better_answer": "一段候选人可直接学习和复述的面试回答，控制在 180 字以内。",
  "key_points": ["最需要记住的点 1", "最需要记住的点 2", "最需要记住的点 3"],
  "next_question": "围绕同一知识点提出一道更简单、更具体的练习追问"
}}

不要责备候选人，不要编造其项目经历。next_question 必须让他能基于刚才的讲解继续回答。
"""


def build_mock_review_prompt(target_job, jd, interview_style, transcript):
    return f"""
你是一名技术面试官。请根据完整模拟面试记录生成简洁复盘。

【岗位】{target_job}
【JD】{jd}
【面试模式】{interview_style}
【面试记录】
{transcript}

使用 Markdown 输出，必须包含：
1. 总体评分（100 分）
2. 做得好的地方（2～4 条）
3. 主要薄弱点（2～4 条）
4. 下次面试前最该练习的 3 件事
5. 一段 120 字以内的整体建议
评价要根据记录，不要泛泛而谈。
"""
