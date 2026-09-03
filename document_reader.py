import io
from pathlib import Path

import easyocr
import fitz
import numpy as np
import pdfplumber
from PIL import Image


ocr_reader = easyocr.Reader(
    ["ch_sim", "en"],
    gpu=False
)
# --------------------------------------------------
# 1. TXT
# --------------------------------------------------

def read_txt(file_path):
    """
    读取 TXT 文件。
    """

    file_path = Path(file_path)

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:
        return file.read()


# --------------------------------------------------
# 2. Markdown
# --------------------------------------------------

def read_md(file_path):
    """
    读取 Markdown 文件。
    Markdown 本质上也是文本文件。
    """

    file_path = Path(file_path)

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:
        return file.read()


# --------------------------------------------------
# 3. 普通 PDF
# --------------------------------------------------

def read_pdf_text(file_path):
    """
    使用 pdfplumber 读取普通文字版 PDF。
    """

    file_path = Path(file_path)

    text_parts = []

    with pdfplumber.open(file_path) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text_parts.append(page_text)

    return "\n".join(text_parts)


# --------------------------------------------------
# 4. 判断 PDF 是否可能需要 OCR
# --------------------------------------------------

def needs_ocr(text, min_chars=100):
    """
    根据直接提取出的文本长度，
    粗略判断 PDF 是否可能是扫描版。

    参数：
        text:
            pdfplumber 提取出的文本

        min_chars:
            少于多少字符时认为可能需要 OCR

    返回：
        bool
    """

    if not text:
        return True

    clean_text = text.strip()

    return len(clean_text) < min_chars


# --------------------------------------------------
# 5. OCR 扫描 PDF
# --------------------------------------------------

def read_pdf_with_ocr(file_path):
    file_path = Path(file_path)

    text_parts = []

    pdf_document = fitz.open(str(file_path))

    for page in pdf_document:

        pix = page.get_pixmap(
            matrix=fitz.Matrix(2, 2)
        )

        image_bytes = pix.tobytes("png")

        image = Image.open(
            io.BytesIO(image_bytes)
        ).convert("RGB")

        image_array = np.array(image)

        results = ocr_reader.readtext(
            image_array,
            detail=1,
            paragraph=False
        )

        # 按“从上到下，再从左到右”排序
        results.sort(
            key=lambda item: (
                item[0][0][1],   # y 坐标
                item[0][0][0]    # x 坐标
            )
        )

        page_text = []

        for box, text, confidence in results:
            if text.strip():
                page_text.append(text.strip())

        if page_text:
            text_parts.append(
                "\n".join(page_text)
            )

    pdf_document.close()

    return "\n\n".join(text_parts)
# --------------------------------------------------
# 6. PDF统一入口
# --------------------------------------------------

def read_pdf(file_path):
    text = read_pdf_text(file_path)

    if needs_ocr(text):
        print(
            f"[document_reader] "
            f"检测到可能是扫描版 PDF，开始 OCR：{file_path}"
        )

        text = read_pdf_with_ocr(file_path)

    return text


# --------------------------------------------------
# 7. 所有文档统一入口
# --------------------------------------------------

def read_document(file_path):
    """
    根据文件扩展名自动选择读取方式。

    无论输入 TXT / MD / PDF，
    最终统一返回 str。
    """

    file_path = Path(file_path)

    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        return read_txt(file_path)

    if suffix == ".md":
        return read_md(file_path)

    if suffix == ".pdf":
        return read_pdf(file_path)

    raise ValueError(
        f"暂不支持的文件类型：{suffix}"
    )