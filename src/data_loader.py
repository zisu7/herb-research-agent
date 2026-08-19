import json
from pathlib import Path

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def load_tcm_herbs():
    with open(_STATIC_DIR / "tcm_828_herbs.json", encoding="utf-8") as f:
        return json.load(f)


def load_food_herbs():
    with open(_STATIC_DIR / "tcm_food_herbs.json", encoding="utf-8") as f:
        return json.load(f)
