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
