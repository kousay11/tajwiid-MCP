import re

_TASHKEEL = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭ࣓-ࣿـ‌‍]")
_ALEF = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي"})


def normalize(text: str) -> str:
    """Letters only: strips tashkeel/tatweel/Quranic marks and unifies alef/ya/ta marbuta forms, for matching."""
    return re.sub(r"\s+", " ", _TASHKEEL.sub("", text).translate(_ALEF)).strip()


def strip_marks(text: str) -> str:
    """Removes only tashkeel/tatweel/Quranic marks. Letter forms are kept, for lookups in sources that spell roots exactly."""
    return _TASHKEEL.sub("", text).strip()
