import shutil
from pathlib import Path
from datetime import datetime


# 当前项目根目录
BASE_DIR = Path(__file__).resolve().parent

# 知识库文件保存目录
KNOWLEDGE_DIR = BASE_DIR / "knowledge" / "interview"

# 如果目录不存在，自动创建
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)


# 当前允许上传的文件类型
ALLOWED_SUFFIXES = {
    ".txt",
    ".md",
    ".pdf"
}


def add_knowledge_files(files):
    """
    把用户上传的知识库文件复制到 knowledge/interview/。

    参数：
        files:
            Gradio File 组件传进来的文件列表。

    返回：
        success_count:
            成功加入的文件数量。

        messages:
            每个文件的处理结果。
    """

    if not files:
        return 0, ["没有选择文件。"]

    success_count = 0
    messages = []

    for file in files:

        # Gradio 上传后的临时文件路径
        source_path = Path(file.name)

        file_name = source_path.name

        suffix = source_path.suffix.lower()

        # 检查扩展名
        if suffix not in ALLOWED_SUFFIXES:
            messages.append(
                f"跳过不支持的文件：{file_name}"
            )
            continue

        # 最终保存位置
        target_path = KNOWLEDGE_DIR / file_name

        # 如果同名文件已经存在，就直接覆盖
        shutil.copy2(
            source_path,
            target_path
        )

        success_count += 1

        messages.append(
            f"已加入：{file_name}"
        )

    return success_count, messages


def load_knowledge_files():
    """
    读取当前知识库目录中的全部文件。

    返回格式：

    [
        ["rag_notes.pdf", "PDF", "2026-09-03 02:20:00"],
        ["python.md", "MD", "2026-09-03 02:21:00"]
    ]

    这个格式可以直接交给 Gradio Dataframe。
    """

    file_rows = []

    for file_path in KNOWLEDGE_DIR.iterdir():

        if not file_path.is_file():
            continue

        suffix = file_path.suffix.lower()

        if suffix not in ALLOWED_SUFFIXES:
            continue

        file_type = suffix.replace(".", "").upper()

        modified_time = datetime.fromtimestamp(
            file_path.stat().st_mtime
        ).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        file_rows.append(
            [
                file_path.name,
                file_type,
                modified_time
            ]
        )

    # 按时间倒序
    file_rows.sort(
        key=lambda row: row[2],
        reverse=True
    )

    return file_rows

def delete_knowledge_file(file_name):
    """
    删除知识库中的指定文件。
    """

    if not file_name:
        return False, "请先选择要删除的文件。"

    file_path = KNOWLEDGE_DIR / file_name

    if not file_path.exists():
        return False, f"文件不存在：{file_name}"

    file_path.unlink()

    return True, f"已删除：{file_name}"