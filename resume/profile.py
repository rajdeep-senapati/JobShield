import json


def load_resume_profile(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_user_preferences(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)
