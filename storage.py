import json
from pathlib import Path
from datetime import datetime

# 当前 storage.py 文件所在的项目目录
BASE_DIR = Path(__file__).resolve().parent

# 公司存档目录：
# AI-Interview-Assistant/data/companies/
COMPANY_DIR = BASE_DIR / "data" / "companies"

# 如果目录不存在，就自动创建
COMPANY_DIR.mkdir(parents=True, exist_ok=True)

# 收藏题库存档目录：
# AI-Interview-Assistant/data/favorites/
FAVORITE_DIR = BASE_DIR / "data" / "favorites"

# 如果目录不存在，就自动创建
FAVORITE_DIR.mkdir(parents=True, exist_ok=True)

def save_company(company_name, target_job, interview_date, jd):
    """
    保存公司信息。
    每家公司保存为一个独立 JSON 文件。
    """

    company_name = company_name.strip()

    if not company_name:
        return False, "公司名称不能为空。"

    company_data = {
        "company_name": company_name,
        "target_job": target_job.strip(),
        "interview_date": interview_date.strip(),
        "jd": jd.strip()
    }

    file_path = COMPANY_DIR / f"{company_name}.json"

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            company_data,
            file,
            ensure_ascii=False,
            indent=4
        )

    return True, f"已保存公司：{company_name}"

def save_favorite(
    question,
    professional_answer,
    simple_answer,
    project_example,
    company_name,
    target_job
):
    """
    保存收藏题目。

    每道收藏题保存为一个独立 JSON 文件。
    """

    if not question:
        return False, "当前没有可收藏的题目。"

    question = question.strip()

    favorite_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    favorite_data = {
        "question": question,
        "professional_answer": professional_answer,
        "simple_answer": simple_answer,
        "project_example": project_example,
        "company_name": company_name,
        "target_job": target_job,
        "favorite_time": favorite_time,

        # 后面做“我的批注”时直接使用
        "note": ""
    }

    # 使用当前收藏文件数量生成简单 ID
    existing_ids = []

    for file_path in FAVORITE_DIR.glob("*.json"):
        try:
            existing_ids.append(int(file_path.stem))
        except ValueError:
            continue

    next_id = max(existing_ids, default=0) + 1

    favorite_id = str(next_id).zfill(4)

    file_path = FAVORITE_DIR / f"{favorite_id}.json"

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            favorite_data,
            file,
            ensure_ascii=False,
            indent=4
        )

    return True, f"已收藏题目：{question}"

def load_companies():
    """
    读取所有已经保存的公司名称。
    返回：
    ["腾讯", "字节跳动", "XX科技有限公司"]
    """

    companies = []

    for file_path in COMPANY_DIR.glob("*.json"):
        companies.append(file_path.stem)

    companies.sort()

    return companies

def load_favorites():
    """
    读取所有收藏题目。

    返回格式：

    [
        {
            "id": "0001",
            "question": "...",
            ...
        }
    ]
    """

    favorites = []

    for file_path in FAVORITE_DIR.glob("*.json"):

        with open(file_path, "r", encoding="utf-8") as file:
            favorite_data = json.load(file)

        favorite_data["id"] = file_path.stem

        favorites.append(favorite_data)

    favorites.sort(
        key=lambda item: item.get("favorite_time", ""),
        reverse=True
    )

    return favorites
def get_company(company_name):
    """
    根据公司名称读取公司详细信息。
    """

    if not company_name:
        return None

    file_path = COMPANY_DIR / f"{company_name}.json"

    if not file_path.exists():
        return None

    with open(file_path, "r", encoding="utf-8") as file:
        company_data = json.load(file)

    return company_data

def get_favorite(favorite_id):
    """
    根据收藏 ID 获取完整收藏数据。
    """

    if not favorite_id:
        return None

    file_path = FAVORITE_DIR / f"{favorite_id}.json"

    if not file_path.exists():
        return None

    with open(file_path, "r", encoding="utf-8") as file:
        favorite_data = json.load(file)

    favorite_data["id"] = favorite_id

    return favorite_data
def delete_company(company_name):
    """
    删除指定公司的 JSON 存档。
    """

    if not company_name:
        return False, "请先选择要删除的公司。"

    file_path = COMPANY_DIR / f"{company_name}.json"

    if not file_path.exists():
        return False, f"没有找到公司：{company_name}"

    file_path.unlink()

    return True, f"已删除公司：{company_name}"
def delete_favorite(favorite_id):
    """
    删除指定收藏题目。
    """

    if not favorite_id:
        return False, "请先选择要取消收藏的题目。"

    file_path = FAVORITE_DIR / f"{favorite_id}.json"

    if not file_path.exists():
        return False, "没有找到该收藏题目。"

    file_path.unlink()

    return True, "已取消收藏。"