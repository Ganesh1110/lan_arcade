"""
Dictionary validation utility for word-based games.
"""
import os
from collections import Counter

_WORDS = None


def get_words_set():
    """Lazily load and return English words set in uppercase."""
    global _WORDS
    if _WORDS is not None:
        return _WORDS

    words = set()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    wordlist_path = os.path.join(base_dir, "wordlist.txt")

    if os.path.exists(wordlist_path):
        try:
            with open(wordlist_path, "r", encoding="utf-8") as f:
                words = {w.strip().upper() for w in f if w.strip()}
        except Exception:
            words = set()

    # Fallback to system dictionary if available
    if len(words) < 100:
        for sys_path in ["/usr/share/dict/words", "/usr/dict/words"]:
            if os.path.exists(sys_path):
                try:
                    with open(sys_path, "r", encoding="utf-8", errors="ignore") as f:
                        words.update(w.strip().upper() for w in f if w.strip().isalpha())
                except Exception:
                    pass

    # Hardcoded minimum safety fallback in case file is absent
    if not words:
        words = {
            "CAT", "DOG", "BAT", "RAT", "SUN", "RUN", "FUN", "BOY", "DAY", "CAR",
            "GAME", "PLAY", "CODE", "TIME", "WORD", "TREE", "BOOK", "FISH", "BIRD",
            "APPLE", "HOUSE", "WATER", "TRAIN", "SMART", "LOGIC", "CODES", "LIGHT",
            "TIGER", "RABBIT", "BANANA", "ORANGE", "SPRING", "SUMMER", "WINTER",
            "COMPUTER", "LANGUAGE", "SOFTWARE", "COLLEGE", "STUDENT", "NETWORK"
        }

    # Common vocabulary additions
    words.update({
        "BOX", "FOX", "OX", "ZOO", "KEY", "MAP", "PEN", "BAG", "BED", "BUS",
        "CUP", "EGG", "HAT", "LEG", "LIP", "MAN", "NET", "PAN", "PIE", "PIG",
        "POT", "RED", "ROD", "ROW", "SEA", "SKY", "TEA", "TOE", "TOP", "TOY",
        "VAN", "WIN", "YES", "ARM", "EYE", "EAR", "ICE", "OIL", "AIR", "AGE"
    })

    # Generate regular inflections (plurals, past tense, present participles)
    # only from genuine base forms, handling consonant doubling properly.
    vowels = set("AEIOU")
    never_double = set("WXYHJKQ")

    def _should_double_consonant(w):
        if len(w) < 3:
            return False
        c = w[-1]
        if c in vowels or c in never_double:
            return False
        v = w[-2]
        if v not in vowels:
            return False
        if len(w) >= 3 and w[-3] in vowels:
            return False
        return True

    def _is_already_inflected(w):
        if w.endswith("ING"):
            if w[:-3] in words or (w[:-3] + "E") in words:
                return True
            if len(w) >= 5 and w[-4] == w[-5] and w[:-4] in words:
                return True
        if w.endswith("ED"):
            if w[:-1] in words or w[:-2] in words:
                return True
            if len(w) >= 5 and w[-3] == w[-4] and w[:-3] in words:
                return True
        if w.endswith("S"):
            if w[:-1] in words:
                return True
            if w.endswith("ES") and w[:-2] in words:
                return True
            if w.endswith("IES") and (w[:-3] + "Y") in words:
                return True
        return False

    inflections = set()
    for w in words:
        if not (2 <= len(w) <= 12):
            continue
        # Do not inflect words that end in participle or past-tense suffixes
        if w.endswith(("ING", "ED")):
            continue
        # Do not inflect already inflected forms
        if _is_already_inflected(w):
            continue

        # 1. Plural / 3rd-person singular
        if w.endswith(("S", "X", "Z", "CH", "SH")):
            inflections.add(w + "ES")
        elif w.endswith("Y") and len(w) > 2 and not w.endswith(("AY", "EY", "OY", "UY")):
            inflections.add(w[:-1] + "IES")
        else:
            inflections.add(w + "S")

        # 2. Past tense and present participle
        if w.endswith("E"):
            inflections.add(w + "D")
            inflections.add(w[:-1] + "ING")
        elif w.endswith("Y") and len(w) > 2 and not w.endswith(("AY", "EY", "OY", "UY")):
            inflections.add(w[:-1] + "IED")
            inflections.add(w + "ING")
        elif _should_double_consonant(w):
            inflections.add(w + w[-1] + "ED")
            inflections.add(w + w[-1] + "ING")
        else:
            inflections.add(w + "ED")
            inflections.add(w + "ING")

    words.update(inflections)
    _WORDS = words
    return _WORDS


def is_valid_word(word):
    """Check if word is in the dictionary (case-insensitive)."""
    if not word or not isinstance(word, str):
        return False
    w = word.strip().upper()
    return w in get_words_set()


def find_anagrams(rack, min_len=3, max_results=20):
    """Find valid dictionary words that can be formed from the rack."""
    if isinstance(rack, str):
        rack = list(rack.upper())
    else:
        rack = [ch.upper() for ch in rack]

    rack_counts = Counter(rack)
    words = get_words_set()
    matches = []

    for w in words:
        if len(w) < min_len or len(w) > len(rack):
            continue
        w_counts = Counter(w)
        if all(rack_counts[c] >= count for c, count in w_counts.items()):
            matches.append(w)
            if len(matches) >= max_results:
                break

    return sorted(matches, key=lambda x: (-len(x), x))
