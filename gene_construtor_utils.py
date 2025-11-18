import re
from difflib import SequenceMatcher
import math

def normalize_text(t: str) -> str:
    if not t:
        return ""
    t = t.lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)       # keep alphanumerics
    t = re.sub(r"\s+", " ", t).strip()
    return t

def token_set(text: str):
    return set(normalize_text(text).split())

def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union > 0 else 0.0

def hybrid_similarity(extract: str, abstract_text: str) -> float:
    """
    Combines 3 signals:
    1. Jaccard token overlap
    2. SequenceMatcher
    3. Important biomedical words overlap
    """
    extract_n = normalize_text(extract)
    abstract_n = normalize_text(abstract_text)

    # token sets
    A = set(extract_n.split())
    B = set(abstract_n.split())

    # 1) Jaccard (token overlap)
    jac = jaccard(A, B)

    # 2) Sequence similarity (good for paraphrasing)
    seq = SequenceMatcher(None, extract_n, abstract_n).ratio()

    # 3) Keyword overlap (biomed nouns: look for words > 5 chars)
    keyA = {w for w in A if len(w) > 5}
    keyB = {w for w in B if len(w) > 5}
    if keyA and keyB:
        key_overlap = len(keyA & keyB) / len(keyA)
    else:
        key_overlap = 0

    # weighted hybrid
    score = (0.4 * jac) + (0.4 * seq) + (0.2 * key_overlap)
    return score