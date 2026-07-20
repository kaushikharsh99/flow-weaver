import hashlib
from typing import List
from flowweaver.std.datasets import Dataset, TabularDataset
from flowweaver.std.utils.validation import validate_dataset, validate_column_exists


def _simhash(text: str) -> int:
    """Computes a 64-bit SimHash fingerprint for string text."""
    tokens = text.lower().split()
    if not tokens:
        return 0
    v = [0] * 64
    for token in tokens:
        token_hash = int(hashlib.md5(token.encode("utf-8")).hexdigest()[:16], 16)
        for i in range(64):
            bit = (token_hash >> i) & 1
            if bit == 1:
                v[i] += 1
            else:
                v[i] -= 1
    fingerprint = 0
    for i in range(64):
        if v[i] >= 0:
            fingerprint |= (1 << i)
    return fingerprint


def _hamming_distance(h1: int, h2: int) -> int:
    """Calculates bitwise Hamming distance between two 64-bit integers."""
    x = h1 ^ h2
    bits = 0
    while x:
        bits += 1
        x &= x - 1
    return bits


def simhash_deduplicate(dataset: Dataset, column: str, threshold: int = 3) -> Dataset:
    """Removes near-duplicate records based on SimHash fingerprint Hamming distance."""
    validate_dataset(dataset)
    validate_column_exists(dataset, column)

    rows = dataset.to_list()
    fingerprints: List[int] = []
    deduped = []

    for r in rows:
        val = str(r.get(column) or "")
        fp = _simhash(val)
        is_near_dup = False

        for existing_fp in fingerprints:
            if _hamming_distance(fp, existing_fp) <= threshold:
                is_near_dup = True
                break

        if not is_near_dup:
            fingerprints.append(fp)
            deduped.append(r)

    res = TabularDataset(
        deduped,
        columns=dataset.columns(),
        metadata=dataset.metadata,
        history=dataset.history
    )
    return res.with_history("simhash_deduplicate", column=column, threshold=threshold)
